"""Cognee mirror — pure-renderer + dispatcher contract.

Mirror behavior is the bridge between AutoCRUD writes and the graph.
The renderer's contract per knowledge-bearing record type:
  - Drafts (agreed=False on RCAReport) are skipped — author signoff
    gates KB entry
  - Agreed reports get tagged with their verification_status as a
    node_set suffix, so the reasoner can weight by manager-signoff trust
  - Glossary, AgentFeedback, DocumentSource each get a stable
    type-specific node_set tag pair

We test the renderer functions directly (they're pure) and the
render_for_cognee dispatcher's type-routing. The async event handler
plumbing (loop scheduling, error swallow) is exercised by the
integration suite end-to-end — not duplicated here.
"""

from __future__ import annotations

import pytest

from rca.adapter.out.autocrud.cognee_mirror import (
    _render_document,
    _render_feedback,
    _render_glossary,
    _render_rca_report,
    render_for_cognee,
)
from rca.domain.agent_feedback import AgentFeedback
from rca.domain.document import DocumentSource
from rca.domain.glossary import GlossaryEntry
from rca.domain.rca_report import RCAReport
from rca.domain.types import VerificationStatus


def test_mirror_skips_draft() -> None:
    """A report without author signoff is a draft — never enters cognee.
    The /sign action requires agreed=True too, so this is the consistent gate."""
    draft = RCAReport(case_study_id="c1", session_id="s1", agreed=False)
    assert _render_rca_report(draft) is None


@pytest.mark.parametrize(
    "status,expected_tag",
    [
        ("unverified", "rca_reports_unverified"),
        ("partial", "rca_reports_partial"),
        ("verified", "rca_reports_verified"),
        ("refuted", "rca_reports_refuted"),
    ],
)
def test_mirror_status_aware_node_set(
    status: VerificationStatus, expected_tag: str
) -> None:
    """Each verification_status maps to a distinct second-tier node_set tag.
    The base "rca_reports" tag is always present too — that's how
    `source_filter="rca_reports"` (the legacy 3-tier filter) keeps working
    even after the 4-tier verification feature lands.

    Reasoner reads the suffix tag at recall time to apply the trust hierarchy
    (verified > partial > unverified ; refuted = case linkage ruled out)."""
    rec = RCAReport(
        case_study_id="c1",
        session_id="s1",
        markdown_content="# test",
        agreed=True,
        verification_status=status,
        signoff_comment="ok" if status == "refuted" else None,
    )
    rendered = _render_rca_report(rec)
    assert rendered is not None
    text, node_set = rendered
    assert "rca_reports" in node_set, "base tag missing — breaks legacy source_filter"
    assert expected_tag in node_set, f"status-suffix tag missing: {expected_tag}"
    assert f"verification_status: {status}" in text, (
        "rendered markdown should expose status to the reasoner"
    )
