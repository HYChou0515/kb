"""Cognee mirror — bridges AutoCRUD writes to the graph for retrieval.

When AutoCRUD creates / updates / patches a knowledge-bearing record
(RCAReport, GlossaryEntry, AgentFeedback, DocumentSource), this handler
renders it to text and pushes it into the graph with the appropriate
node_set provenance tag.

For RCAReport, node_set is **status-aware** — the verification_status
field controls the second tag (rca_reports_unverified / partial /
verified / refuted), letting the reasoner weight by manager-signoff
trust at recall time.

The graph never stores the AutoCRUD record itself — only its textual
projection indexed for /recall.

Cognify is NOT triggered per-record (too expensive). Call /admin/cognify
explicitly after batch writes.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from autocrud.types import (
    AfterCreate,
    AfterPatch,
    AfterUpdate,
    EventContext,
    IEventHandler,
)

from rca.domain.agent_feedback import AgentFeedback
from rca.domain.document import DocumentSource
from rca.domain.glossary import GlossaryEntry
from rca.domain.rca_report import RCAReport
from rca.ports.out.graph import GraphClient

logger = logging.getLogger(__name__)


# ─── per-type renderers ─────────────────────────────────────────────────────

_RCA_NODE_SET: dict[str, list[str]] = {
    "unverified": ["rca_reports", "rca_reports_unverified"],
    "partial":    ["rca_reports", "rca_reports_partial"],
    "verified":   ["rca_reports", "rca_reports_verified"],
    "refuted":    ["rca_reports", "rca_reports_refuted"],
}


def _render_rca_report(rec: RCAReport) -> tuple[str, list[str]] | None:
    if not rec.agreed:
        # Drafts are not mirrored — author signoff is the gate.
        return None
    text = (
        f"# RCA Report ({rec.verification_status})\n"
        f"*case_study_id: {rec.case_study_id} | session_id: {rec.session_id} | "
        f"agreed_at: {rec.agreed_at} | signed_off_by: {rec.signed_off_by} | "
        f"verification_status: {rec.verification_status} | "
        f"verified_by: {rec.verified_by or '(unsigned)'} | "
        f"signoff_comment: {rec.signoff_comment or ''}*\n\n"
        f"{rec.markdown_content}"
    )
    return text, _RCA_NODE_SET[rec.verification_status]


def _render_glossary(rec: GlossaryEntry) -> tuple[str, list[str]] | None:
    text = (
        f"## Glossary entry: {rec.term}\n"
        f"- **Expansion:** {rec.expansion}\n"
        f"- **Context:** {rec.context}\n"
        f"- **Confidence:** {rec.confidence}\n"
        f"- **Source session:** {rec.source_session_id or '(unknown)'}\n"
    )
    return text, ["rca_conversations", "rca_glossary"]


def _render_feedback(rec: AgentFeedback) -> tuple[str, list[str]] | None:
    text = (
        f"## Agent feedback ({rec.type}): {rec.topic}\n"
        f"- **Agent said:** {rec.agent_said}\n"
        f"- **Expert correction:** {rec.expert_correction}\n"
        f"- **Learning for agent:** {rec.learning_for_agent}\n"
        f"- **Source session:** {rec.source_session_id or '(unknown)'}\n"
    )
    return text, ["rca_conversations", "rca_agent_feedback"]


_DOCUMENT_NODE_SET: dict[str, list[str]] = {
    "literature": ["rca_literature"],
    "primer": ["rca_literature", "rca_primer"],
    "rca_report_md": ["rca_reports"],
    "conversation_extracted": ["rca_conversations"],
}


def _render_document(rec: DocumentSource) -> tuple[str, list[str]] | None:
    text = f"# {rec.label}\n*source_kind: {rec.source_kind}*\n\n{rec.text}"
    node_set = _DOCUMENT_NODE_SET.get(rec.source_kind, ["rca_literature"])
    return text, node_set


_RENDERERS: dict[type, Any] = {
    RCAReport: _render_rca_report,
    GlossaryEntry: _render_glossary,
    AgentFeedback: _render_feedback,
    DocumentSource: _render_document,
}


def render_for_cognee(record: Any) -> tuple[str, list[str]] | None:
    """Dispatch to the right renderer; return None if the record type is
    not knowledge-bearing or rendering bailed (e.g. draft RCAReport)."""
    renderer = _RENDERERS.get(type(record))
    if renderer is None:
        return None
    return renderer(record)


# ─── event handler ──────────────────────────────────────────────────────────


_MIRROR_CONTEXTS = (AfterCreate, AfterUpdate, AfterPatch)


class CogneeMirrorHandler(IEventHandler):
    """AutoCRUD event handler that mirrors knowledge-bearing writes to the graph.

    Drops the legacy module globals (`_cognee` / `_dataset`); takes the
    GraphClient and dataset name in `__init__`. Multiple instances per
    process are now valid (e.g. one per dataset).

    `is_supported()` filters down to only After* contexts on knowledge-
    bearing record types, so AutoCRUD doesn't even ask us about lifecycle
    models (CaseStudy / Session) or read events.

    We don't react to deletes — chunk-level delete in cognee is messy and
    POC scope is append-only. A status update (e.g. unverified → verified)
    re-mirrors a new chunk under the new node_set; the old chunk remains
    until v2 implements proper chunk lifecycle tracking.
    """

    def __init__(self, graph: GraphClient, *, dataset: str = "rca") -> None:
        self._graph = graph
        self._dataset = dataset

    def is_supported(self, context: EventContext) -> bool:
        if not isinstance(context, _MIRROR_CONTEXTS):
            return False
        record = getattr(context, "data", None)
        if record is None:
            return False
        return type(record) in _RENDERERS

    def handle_event(self, context: EventContext) -> None:
        record = getattr(context, "data", None)
        if record is None:
            return

        rendered = render_for_cognee(record)
        if rendered is None:
            return
        text, node_set = rendered
        type_name = type(record).__name__

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(self._push(text, node_set, type_name))
            except Exception as exc:  # noqa: BLE001
                logger.error("cognee mirror failed (sync path) for %s: %s", type_name, exc)
            return

        loop.create_task(self._push(text, node_set, type_name))

    async def _push(self, text: str, node_set: list[str], type_name: str) -> None:
        try:
            await self._graph.add_text(text, dataset=self._dataset, node_set=node_set)
            logger.info(
                "mirrored %s → cognee (node_set=%s, %d chars)",
                type_name,
                node_set,
                len(text),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("cognee mirror failed for %s: %s", type_name, exc)
