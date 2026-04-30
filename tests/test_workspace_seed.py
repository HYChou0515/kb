"""Workspace seeding — first-time workspace gets template files + rendered CASE.md.

When a user opens a workspace for a freshly-created CaseStudy (no prior
workspace_archive blob), the active_dir is empty. We seed it with:

  - Static template files (AGENTS.md, README.md, notes.md, draft_report.md,
    .gitignore, .opencode/agents/) — copied verbatim from
    `templates/case_workspace/`. These give opencode its agent instructions
    and give the user a familiar workspace skeleton.

  - CASE.md — rendered programmatically from the CaseStudy struct fields
    (title, description, defect_type, etc.). This is the case-specific
    context that the agent reads as part of its initial context.

CASE.md is ALWAYS overwritten on open-workspace because the CaseStudy
record is the authoritative source of case metadata; users edit
CaseStudy fields via the AutoCRUD PATCH endpoint, not by editing
CASE.md inside the workspace.

opencode.json is intentionally NOT in the template — opencode config is
injected via env vars (OPENCODE_DISABLE_PROJECT_CONFIG=true +
OPENCODE_CONFIG_CONTENT) at spawn time so the agent cannot self-modify
its own constraints.
"""

from __future__ import annotations

from pathlib import Path

from rca.domain.case_study import CaseStudy
from rca.services.workspace_seed import seed_workspace


def test_seed_creates_template_files_and_rendered_case_md(tmp_path: Path) -> None:
    """First-time workspace seed: template tree copied + CASE.md rendered with
    case fields. Load-bearing contract — opencode launches into a workspace
    that already has agent instructions and case context, not an empty dir."""
    case = CaseStudy(
        title="Cu via resistance spike on M2",
        description="Yield drop on post-CMP M2 chain test",
        defect_type="via_open",
        process_module="BEOL",
        scan_stage="post-M2-CMP",
        owner="alice",
        tags=["damascene", "28nm"],
    )

    seed_workspace(case, tmp_path)

    # Static template files copied
    assert (tmp_path / "AGENTS.md").exists(), (
        "AGENTS.md missing — opencode reads this for agent instructions"
    )
    assert (tmp_path / "README.md").exists(), "human-facing README.md missing"
    assert (tmp_path / "notes.md").exists(), "notes.md skeleton missing"
    assert (tmp_path / "draft_report.md").exists(), "draft_report.md skeleton missing"
    assert (tmp_path / ".gitignore").exists(), ".gitignore missing"

    # opencode.json must NOT be in the template (security: env-injected only)
    assert not (tmp_path / "opencode.json").exists(), (
        "opencode.json must not be seeded — config is env-injected to prevent "
        "agent self-modification of its own constraints"
    )

    # CASE.md rendered from case fields
    case_md = (tmp_path / "CASE.md").read_text(encoding="utf-8")
    assert "Cu via resistance spike on M2" in case_md
    assert "Yield drop on post-CMP M2 chain test" in case_md
    assert "via_open" in case_md
    assert "BEOL" in case_md
    assert "post-M2-CMP" in case_md
    assert "alice" in case_md


def test_seed_idempotent_on_resume_does_not_clobber_user_edits(
    tmp_path: Path,
) -> None:
    """When called a second time on a workspace that already has user edits
    in notes.md, those edits MUST survive — seed_workspace is for first-time
    or resume-after-untar; it never overwrites mutable user files.

    CASE.md is the exception: always re-rendered (case metadata is
    authoritative)."""
    case = CaseStudy(
        title="Test case",
        description="d",
    )

    seed_workspace(case, tmp_path)

    # Simulate user (or agent) writing into notes.md
    (tmp_path / "notes.md").write_text(
        "# My notes\nObserved A→B at step 3", encoding="utf-8"
    )

    # Second seed (e.g., resume path re-runs seed defensively)
    seed_workspace(case, tmp_path)

    # User edits preserved
    notes = (tmp_path / "notes.md").read_text(encoding="utf-8")
    assert "Observed A→B at step 3" in notes, (
        "second seed clobbered user edits in notes.md"
    )


def test_seed_renders_optional_fields_gracefully(tmp_path: Path) -> None:
    """CaseStudy fields like defect_type / process_module / scan_stage are
    Optional — CASE.md must render readable text for None values, not crash
    or print 'None'."""
    case = CaseStudy(
        title="Minimal case",
        description="just a title and description",
        # everything else default (defect_type/process_module/scan_stage = None, tags = [])
    )

    seed_workspace(case, tmp_path)

    case_md = (tmp_path / "CASE.md").read_text(encoding="utf-8")
    assert "Minimal case" in case_md
    # Whatever placeholder is used, "None" itself shouldn't leak
    assert "None" not in case_md, f"CASE.md leaked Python None into output: {case_md!r}"
