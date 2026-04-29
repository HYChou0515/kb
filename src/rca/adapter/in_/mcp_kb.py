"""kb-mcp — in-process MCP server using KBService directly.

Replaces the legacy HTTP-proxy `mcp_servers/kb_mcp.py`. Tools surface
preserved at the MCP protocol level (same tool names + parameter shapes
as the deleted server), so MCP-side callers see no contract change.
Wiring changed from HTTP → in-process via the dep-injector Container.

Run:
    uv run kb-mcp                 # console script (stdio transport)
    uv run python -m adapter.in_.mcp_kb
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from rca.container import Container
from rca.ports.in_.recall import RecallRequest, SourceFilter
from rca.ports.in_.retain import (
    ExtractionResult,
    RetainConversationRequest,
    RetainExtractionRequest,
    RetainTextRequest,
)

logger = logging.getLogger(__name__)


SourceKind = Literal["literature", "conversation", "rca_report"]


mcp = FastMCP("kb-mcp")

_container: Container | None = None


def _kb():
    global _container
    if _container is None:
        _container = Container()
    return _container.kb()


@mcp.tool()
async def retain_text(
    text: str,
    label: str = "inline",
    source_kind: SourceKind = "literature",
    cognify: bool = True,
) -> dict[str, Any]:
    """Push raw text into the KB. KB will run LLM extraction internally.

    `source_kind` controls the provenance / trust tier:
      - "literature"   — textbooks, papers, process docs (lowest trust)
      - "conversation" — live RCA discussion transcript
      - "rca_report"   — agreed-and-finalized RCA report markdown

    Note: RCA reports are layered further by manager-signoff status
    (unverified / partial / verified / refuted). Use the /sign action
    on the resulting RCAReport to elevate trust.
    """
    req = RetainTextRequest(
        text=text, label=label, source_kind=source_kind, cognify=cognify
    )
    resp = await _kb().retain_text(req)
    return resp.model_dump()


@mcp.tool()
async def retain_conversation(
    messages: list[dict],
    session_id: str | None = None,
    cognify: bool = True,
) -> dict[str, Any]:
    """Ingest an RCA conversation transcript."""
    req = RetainConversationRequest(
        messages=messages, session_id=session_id, cognify=cognify
    )
    resp = await _kb().retain_conversation(req)
    return resp.model_dump()


@mcp.tool()
async def retain_extraction(
    extraction: dict[str, Any],
    source_label: str,
    source_kind: SourceKind = "literature",
    cognify: bool = True,
) -> dict[str, Any]:
    """Push pre-extracted structured knowledge directly into the KB."""
    req = RetainExtractionRequest(
        extraction=ExtractionResult.model_validate(extraction),
        source_label=source_label,
        source_kind=source_kind,
        cognify=cognify,
    )
    resp = await _kb().retain_extraction(req)
    return resp.model_dump()


@mcp.tool()
async def recall_assessment(
    query: str,
    process_context: str | None = None,
    source_filter: SourceFilter = "all",
    top_k: int = 12,
) -> dict[str, Any]:
    """★ Primary tool for step 8 of the RCA flow. Structured causal assessment."""
    req = RecallRequest(
        query=query,
        mode="assessment",
        process_context=process_context,
        source_filter=source_filter,
        top_k=top_k,
    )
    resp = await _kb().recall(req)
    return resp.model_dump()


@mcp.tool()
async def recall_snippets(
    query: str,
    source_filter: SourceFilter = "all",
    top_k: int = 8,
    exclude_refuted: bool = False,
) -> dict[str, Any]:
    """Cheap retrieval of raw KG snippets — no LLM synthesis.

    `exclude_refuted=True` drops snippets tagged as rca_reports_refuted
    (case-level attribution disproven; use when you only want positive
    knowledge, not ruled-out hypotheses).
    """
    req = RecallRequest(
        query=query,
        mode="snippets",
        source_filter=source_filter,
        top_k=top_k,
        exclude_refuted=exclude_refuted,
    )
    resp = await _kb().recall(req)
    return resp.model_dump()


@mcp.tool()
async def recall_synthesis(query: str, top_k: int = 8) -> dict[str, Any]:
    """Get a free-text synthesized answer (cognee GRAPH_COMPLETION)."""
    req = RecallRequest(query=query, mode="synthesis", top_k=top_k)
    resp = await _kb().recall(req)
    return resp.model_dump()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    mcp.run()


if __name__ == "__main__":
    main()
