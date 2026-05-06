"""Workspace dir + case metadata management for rca_ui.

Each case gets a directory under <workspace_root>/<case_id>/ with:

    case.json          — case metadata (title, owner, defect_type, …)
                         AUTHORITATIVE source of truth, owned by rca_ui.
    CASE.md            — auto-rendered from case.json on every open.
    README.md          — boilerplate for human visitors.
    notes.md           — agent + user scratchpad.
    draft_report.md    — co-authored draft.
    transcript.jsonl   — append-only message log (session_store owns).
    session.json       — current session state (session_store owns).
    .git/              — for git-based file viewers.

There's no kb-api involvement in case metadata — kb-api is the
knowledge graph, not the case registry. UI's index page enumerates
cases by listing this directory.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SEED_FILES = {
    "README.md": (
        "# RCA case workspace\n\n"
        "This directory is the working environment for one defect-RCA case.\n"
        "Files here are visible to the agent via the MCP filesystem tool.\n\n"
        "## Files\n\n"
        "| File | Purpose |\n|---|---|\n"
        "| `case.json` | case metadata (authoritative; UI edits this) |\n"
        "| `CASE.md` | auto-rendered from case.json (do not edit directly) |\n"
        "| `notes.md` | scratchpad for cumulative observations |\n"
        "| `draft_report.md` | co-authored draft of the RCA report |\n"
        "| `transcript.jsonl` | append-only message log |\n"
        "| `session.json` | current session state |\n"
    ),
    "notes.md": (
        "# Notes\n\n"
        "Cumulative observations across the RCA conversation. The agent\n"
        "appends here as facts emerge; you can also edit directly.\n\n---\n"
    ),
    "draft_report.md": (
        "# RCA Report — DRAFT\n\n"
        "## Defect Summary\n\n(...)\n\n"
        "## Confirmed Root Cause\n\n(...)\n\n"
        "## Ruled-out Hypotheses\n\n(...)\n\n"
        "## Confounders\n\n(...)\n\n"
        "## Action Items\n\n(...)\n\n"
        "## Knowledge Gaps\n\n(...)\n"
    ),
}

_CASE_MD_TEMPLATE = """\
# Case: {title}

| Field | Value |
|---|---|
| **Owner** | {owner} |
| **Defect type** | {defect_type} |
| **Process module** | {process_module} |
| **Scan stage** | {scan_stage} |
| **Tags** | {tags} |

## Description

{description}

---

*Auto-rendered from case.json on every open-workspace. To change case
metadata, edit case.json (or use the UI's edit form); do NOT edit this
file — your edits are overwritten on the next open.*
"""

CASE_JSON = "case.json"


@dataclass
class CaseMeta:
    """Authoritative case metadata. Stored as <workspace>/case.json."""

    id: str
    title: str
    description: str = ""
    owner: str = "unknown"
    status: str = "active"  # active | closed
    defect_type: str | None = None
    process_module: str | None = None
    scan_stage: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CaseMeta:
        kwargs = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**kwargs)


def workspace_dir(workspace_root: Path, case_id: str) -> Path:
    """Path of a case's workspace dir. Pure function — does not create."""
    return workspace_root / _safe_segment(case_id)


def new_case_id() -> str:
    """Generate a fresh case_id. Format mirrors the legacy AutoCRUD
    `case-study:<uuid>` for downstream stability."""
    return f"case-study:{uuid.uuid4()}"


def create_case(
    workspace_root: Path,
    *,
    title: str,
    description: str = "",
    owner: str = "unknown",
    defect_type: str | None = None,
    process_module: str | None = None,
    scan_stage: str | None = None,
    tags: list[str] | None = None,
) -> CaseMeta:
    """Create a new case (assigns a fresh case_id, writes case.json + seeds).
    Returns the populated CaseMeta."""
    case_id = new_case_id()
    now = _now_iso()
    meta = CaseMeta(
        id=case_id,
        title=title,
        description=description,
        owner=owner,
        defect_type=defect_type,
        process_module=process_module,
        scan_stage=scan_stage,
        tags=tags or [],
        created_at=now,
        updated_at=now,
    )
    dest = workspace_dir(workspace_root, case_id)
    dest.mkdir(parents=True, exist_ok=True)
    save_case(dest, meta)
    _seed_files(dest)
    _render_case_md(dest, meta)
    _ensure_git_repo(dest)
    return meta


def open_case(workspace_root: Path, case_id: str) -> tuple[Path, CaseMeta]:
    """Open an existing case (or fail if it doesn't exist).
    Re-renders CASE.md, ensures seed files, idempotent git init.
    Returns (workspace_path, meta)."""
    dest = workspace_dir(workspace_root, case_id)
    if not (dest / CASE_JSON).exists():
        raise FileNotFoundError(
            f"No case found at {dest} — did you run create_case first?"
        )
    meta = load_case(dest)
    _seed_files(dest)
    _render_case_md(dest, meta)
    _ensure_git_repo(dest)
    return dest, meta


def list_cases(workspace_root: Path) -> list[CaseMeta]:
    """Enumerate all cases by scanning <workspace_root>/*/case.json.
    Sorted by created_at descending (newest first)."""
    if not workspace_root.exists():
        return []
    out: list[CaseMeta] = []
    for child in workspace_root.iterdir():
        if not child.is_dir():
            continue
        cj = child / CASE_JSON
        if not cj.exists():
            continue
        try:
            out.append(load_case(child))
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("skipping malformed case at %s: %s", child, exc)
    out.sort(key=lambda m: m.created_at or "", reverse=True)
    return out


def load_case(workspace: Path) -> CaseMeta:
    raw = json.loads((workspace / CASE_JSON).read_text(encoding="utf-8"))
    return CaseMeta.from_dict(raw)


def save_case(workspace: Path, meta: CaseMeta) -> None:
    meta.updated_at = _now_iso()
    (workspace / CASE_JSON).write_text(
        json.dumps(meta.to_dict(), ensure_ascii=False, indent=2), "utf-8"
    )


# ─── helpers ─────────────────────────────────────────────────────────────


def _seed_files(dest: Path) -> None:
    for name, body in _SEED_FILES.items():
        target = dest / name
        if not target.exists():
            target.write_text(body, encoding="utf-8")


def _render_case_md(dest: Path, meta: CaseMeta) -> None:
    text = _CASE_MD_TEMPLATE.format(
        title=meta.title or "(untitled)",
        owner=meta.owner or "(unknown)",
        defect_type=meta.defect_type or "(unspecified)",
        process_module=meta.process_module or "(unspecified)",
        scan_stage=meta.scan_stage or "(unspecified)",
        tags=", ".join(meta.tags) if meta.tags else "(none)",
        description=meta.description or "",
    )
    (dest / "CASE.md").write_text(text, encoding="utf-8")


def _safe_segment(case_id: str) -> str:
    """case_id is `case-study:<uuid>` — colons are valid on POSIX but trip
    up some tooling, so we collapse to a flat name."""
    return case_id.replace(":", "_").replace("/", "_")


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _ensure_git_repo(dest: Path) -> None:
    """`git init` + seed commit so file-tree tooling has something to
    enumerate. Idempotent."""
    if not (dest / ".git").exists():
        try:
            subprocess.run(
                ["git", "init", "-q", "-b", "main"],
                cwd=dest,
                check=True,
                capture_output=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            logger.warning("git init failed for %s: %s", dest, exc)
            return

    head_check = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", "HEAD"],
        cwd=dest,
        capture_output=True,
    )
    if head_check.returncode == 0:
        return

    env = {
        "GIT_AUTHOR_NAME": "rca-ui",
        "GIT_AUTHOR_EMAIL": "rca-ui@local",
        "GIT_COMMITTER_NAME": "rca-ui",
        "GIT_COMMITTER_EMAIL": "rca-ui@local",
    }
    try:
        subprocess.run(["git", "add", "-A"], cwd=dest, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "seed workspace", "--allow-empty"],
            cwd=dest,
            check=True,
            capture_output=True,
            env={**os.environ, **env},
        )
    except subprocess.CalledProcessError as exc:
        logger.warning("seed commit failed: %s", exc.stderr or exc)


def archive_workspace(dest: Path, archive_path: Path) -> None:
    """tar.gz the workspace into `archive_path` (used at session close
    for audit trail). Idempotent overwrite."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    base = archive_path.with_suffix("").with_suffix("")  # strip .tar.gz
    shutil.make_archive(str(base), "gztar", root_dir=str(dest))
