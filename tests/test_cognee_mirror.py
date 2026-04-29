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
from rca.domain.types import DocumentKind, VerificationStatus


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


# ─── glossary / feedback ─────────────────────────────────────────────────────


def test_glossary_renders_term_and_node_set() -> None:
    """Glossary entries land in `rca_glossary` (under `rca_conversations` umbrella)
    so /recall can scope to expert vocabulary lookups separately from RCA reports."""
    entry = GlossaryEntry(
        term="ABC123",
        expansion="Asymmetric Backside Contamination",
        context="contamination signature seen on tool ETCH-04",
        source_session_id="sess-1",
    )
    rendered = _render_glossary(entry)
    assert rendered is not None
    text, node_set = rendered
    assert node_set == ["rca_conversations", "rca_glossary"]
    assert "ABC123" in text
    assert "Asymmetric Backside Contamination" in text


def test_feedback_renders_correction_and_node_set() -> None:
    """Agent feedback gets its own tag so the reasoner can lookup
    "what did experts correct me on for X" separately from glossary."""
    fb = AgentFeedback(
        type="correction",
        topic="defect classification",
        agent_said="this is a particle defect",
        expert_correction="actually it's pattern collapse — different mechanism",
        learning_for_agent="differentiate by edge profile",
        source_session_id="sess-2",
    )
    rendered = _render_feedback(fb)
    assert rendered is not None
    text, node_set = rendered
    assert node_set == ["rca_conversations", "rca_agent_feedback"]
    assert "pattern collapse" in text
    assert "(correction)" in text


# ─── document source kinds ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "source_kind,expected_node_set",
    [
        ("literature", ["rca_literature"]),
        ("primer", ["rca_literature", "rca_primer"]),
        ("rca_report_md", ["rca_reports"]),
        ("conversation_extracted", ["rca_conversations"]),
    ],
)
def test_document_source_kind_routes_to_node_set(
    source_kind: DocumentKind, expected_node_set: list[str]
) -> None:
    """Each DocumentKind has a stable target node_set so source-aware
    retrieval (e.g. "search primers only") works at recall time. If this
    table drifts from _DOCUMENT_NODE_SET in the source module, the
    primer corpus test in tests/integration/ will also break."""
    doc = DocumentSource(label="x", source_kind=source_kind, text="body")
    rendered = _render_document(doc)
    assert rendered is not None
    text, node_set = rendered
    assert node_set == expected_node_set
    assert "body" in text


# ─── dispatcher ──────────────────────────────────────────────────────────────


def test_dispatcher_returns_none_for_unknown_type() -> None:
    """render_for_cognee is the gate that decides "is this record knowledge-
    bearing?" — non-knowledge types (CaseStudy, Session, etc.) MUST return
    None so the mirror handler doesn't push lifecycle records into the graph."""

    class NotKnowledge:
        pass

    assert render_for_cognee(NotKnowledge()) is None


def test_dispatcher_routes_to_correct_renderer() -> None:
    """Spot-check that the dispatch table picks the right renderer per type —
    catches accidental swaps in _RENDERERS that would silently misroute."""
    glossary_result = render_for_cognee(
        GlossaryEntry(term="t", expansion="e", context="c")
    )
    assert glossary_result is not None
    _, ns = glossary_result
    assert "rca_glossary" in ns

    feedback_result = render_for_cognee(
        AgentFeedback(
            type="confirmation",
            topic="t",
            agent_said="a",
            expert_correction="b",
            learning_for_agent="c",
        )
    )
    assert feedback_result is not None
    _, ns = feedback_result
    assert "rca_agent_feedback" in ns
