"""Cognee mirror — bridge from AutoCRUD writes to cognee's retrieval index.

When AutoCRUD creates / updates / patches a knowledge-bearing record
(RCAReport, GlossaryEntry, AgentFeedback, DocumentSource), this handler
renders it to text and pushes it into cognee with the appropriate
node_set provenance tag.

Cognee never stores the AutoCRUD record itself — only its textual projection
indexed for /recall.

Cognify is NOT triggered per-record (too expensive). Call /admin/cognify
explicitly after batch writes (seed_corpus.py, seed_primer.py) or via
the agent at session close.
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

from kb_api.models import (
    AgentFeedback,
    DocumentSource,
    GlossaryEntry,
    RCAReport,
)
from rca_knowledge.graph.cognee_client import CogneeClient

logger = logging.getLogger(__name__)


# Module-level singleton — set by the FastAPI lifespan once cognee is up.
_cognee: CogneeClient | None = None
_dataset: str = "rca"


def configure_mirror(cognee: CogneeClient, *, dataset: str = "rca") -> None:
    """Called once at app startup to bind the mirror to a live cognee client."""
    global _cognee, _dataset
    _cognee = cognee
    _dataset = dataset
    logger.info("cognee mirror configured (dataset=%s)", dataset)


# ─── per-type renderers ─────────────────────────────────────────────────────


def _render_rca_report(rec: RCAReport) -> tuple[str, list[str]] | None:
    if not rec.agreed:
        # Drafts are not mirrored — only the 1st-truth tier (agreed reports).
        return None
    text = (
        f"# RCA Report\n"
        f"*case_study_id: {rec.case_study_id} | session_id: {rec.session_id} | "
        f"agreed_at: {rec.agreed_at} | signed_off_by: {rec.signed_off_by}*\n\n"
        f"{rec.markdown_content}"
    )
    return text, ["rca_reports"]


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
    """Dispatch to the right renderer; return None if record type is not
    knowledge-bearing (e.g. CaseStudy, Session) or rendering bailed (e.g.
    draft RCAReport)."""
    renderer = _RENDERERS.get(type(record))
    if renderer is None:
        return None
    return renderer(record)


# ─── event handler ──────────────────────────────────────────────────────────


# AutoCRUD context types we react to. Modify is intentionally NOT mirrored —
# `modify` edits drafts in-place; we only mirror published writes.
_MIRROR_CONTEXTS = (AfterCreate, AfterUpdate, AfterPatch)


class CogneeMirrorHandler(IEventHandler):
    """AutoCRUD event handler that mirrors knowledge-bearing writes to cognee.

    `is_supported()` filters down to only the After* contexts on knowledge-
    bearing record types, so AutoCRUD doesn't even ask us about lifecycle
    models (CaseStudy / Session) or read events.

    We don't react to deletes — cognee's chunk-level delete is messy and
    POC scope is append-only. If a record gets deleted, the corresponding
    cognee chunks become stale; live with it for POC. v2 should track
    chunk IDs per AutoCRUD record and delete on demand.
    """

    def is_supported(self, context: EventContext) -> bool:
        if not isinstance(context, _MIRROR_CONTEXTS):
            return False
        record = getattr(context, "data", None)
        if record is None:
            return False
        return type(record) in _RENDERERS

    def handle_event(self, context: EventContext) -> None:
        """AutoCRUD calls this synchronously. We schedule the actual cognee
        write as a background task on the running event loop (FastAPI's),
        so we don't block the AutoCRUD write path on a slow LLM/embedding call.
        """
        if _cognee is None:
            logger.debug("mirror not configured yet, skipping %s", type(context).__name__)
            return

        record = getattr(context, "data", None)
        if record is None:
            return

        rendered = render_for_cognee(record)
        if rendered is None:
            return  # not knowledge-bearing or skipped (e.g. draft RCAReport)
        text, node_set = rendered
        type_name = type(record).__name__

        # Try to schedule on the running loop (FastAPI request context).
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No loop — running outside FastAPI (e.g. CLI). Block-execute.
            try:
                asyncio.run(_push_to_cognee(text, node_set, type_name))
            except Exception as exc:  # noqa: BLE001
                logger.error("cognee mirror failed (sync path) for %s: %s", type_name, exc)
            return

        # Fire-and-forget on the running loop.
        loop.create_task(_push_to_cognee(text, node_set, type_name))


async def _push_to_cognee(text: str, node_set: list[str], type_name: str) -> None:
    """Background task: actually write to cognee. Errors are logged, not raised
    (mirror is best-effort; AutoCRUD write already succeeded)."""
    try:
        await _cognee.add_text(text, dataset=_dataset, node_set=node_set)  # type: ignore[union-attr]
        logger.info(
            "mirrored %s → cognee (node_set=%s, %d chars)",
            type_name,
            node_set,
            len(text),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("cognee mirror failed for %s: %s", type_name, exc)
