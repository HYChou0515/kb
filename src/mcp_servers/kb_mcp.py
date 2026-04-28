"""kb-mcp — thin MCP proxy to the KB API.

Exposes retain_* and recall_* tools that the OpenCode agent uses during
the RCA flow. All calls forward to the FastAPI app at $KB_API_BASE_URL.

Run:
    uv run kb-mcp                 # console script (stdio transport)
    uv run python -m mcp_servers.kb_mcp
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

KB_BASE = os.getenv("KB_API_BASE_URL", "http://127.0.0.1:8765")

mcp = FastMCP("kb-mcp")


def _client() -> httpx.AsyncClient:
    # Generous timeout — extraction/cognify can take a while on large inputs.
    return httpx.AsyncClient(base_url=KB_BASE, timeout=httpx.Timeout(300.0))


@mcp.tool()
async def retain_text(
    text: str,
    label: str = "inline",
    source_kind: str = "literature",
    cognify: bool = True,
) -> dict[str, Any]:
    """Push raw text into the KB. KB will run LLM extraction internally.

    `source_kind` controls the provenance / trust tier:
      - "literature"   — textbooks, papers, process docs (lowest trust)
      - "conversation" — live RCA discussion transcript
      - "rca_report"   — agreed-and-finalized RCA report markdown (HIGHEST trust;
                          fab-validated outcome)

    The reasoner gives rca_report-sourced snippets higher weight when synthesizing
    causal assessments. Use rca_report when ingesting the markdown produced at
    step 9 of the RCA agent flow.
    """
    async with _client() as c:
        r = await c.post(
            "/retain/text",
            json={"text": text, "label": label, "source_kind": source_kind, "cognify": cognify},
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def retain_conversation(
    messages: list[dict],
    session_id: str | None = None,
    cognify: bool = True,
) -> dict[str, Any]:
    """Ingest an RCA conversation transcript. KB extracts confirmed
    causal claims (and ruled-out hypotheses) and stores them as
    conversation-sourced knowledge.

    `messages` format: [{"role": "user"|"assistant", "content": "..."}]
    """
    async with _client() as c:
        r = await c.post(
            "/retain/conversation",
            json={"messages": messages, "session_id": session_id, "cognify": cognify},
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def retain_extraction(
    extraction: dict[str, Any],
    source_label: str,
    source_kind: str = "literature",
    cognify: bool = True,
) -> dict[str, Any]:
    """Push pre-extracted structured knowledge directly into the KB.

    `extraction` must conform to the ExtractionResult schema:
    {entities: [{name,type,...}], relations: [{source,target,type,mechanism,...}], summary}
    """
    async with _client() as c:
        r = await c.post(
            "/retain/extraction",
            json={
                "extraction": extraction,
                "source_label": source_label,
                "source_kind": source_kind,
                "cognify": cognify,
            },
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def recall_assessment(
    query: str,
    process_context: str | None = None,
    source_filter: str = "all",
    top_k: int = 12,
) -> dict[str, Any]:
    """★ Primary tool for step 8 of the RCA flow.

    Ask the KB whether a (factor → defect) candidate has a plausible causal
    mechanism. Returns a structured assessment:
        verdict: plausible | uncertain | implausible
        mechanisms: [...]
        confounders: [...]
        suggested_investigations: [...]
        knowledge_gaps: [...]

    `query` should describe the candidate, e.g.
        "Tool ETCH_C at step M2_VIA_ETCH correlates with M2 metal short defects"
    `process_context` adds layer/module/node info.
    """
    async with _client() as c:
        r = await c.post(
            "/recall",
            json={
                "query": query,
                "mode": "assessment",
                "process_context": process_context,
                "source_filter": source_filter,
                "top_k": top_k,
            },
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def recall_snippets(
    query: str,
    source_filter: str = "all",
    top_k: int = 8,
) -> dict[str, Any]:
    """Cheap retrieval of raw KG snippets — no LLM synthesis.

    Use when you (the agent) want to look something up generally without
    triggering the full causal-assessment LLM call.
    """
    async with _client() as c:
        r = await c.post(
            "/recall",
            json={
                "query": query,
                "mode": "snippets",
                "source_filter": source_filter,
                "top_k": top_k,
            },
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def recall_synthesis(query: str, top_k: int = 8) -> dict[str, Any]:
    """Get a free-text synthesized answer (cognee GRAPH_COMPLETION).

    Use for step 9 report writing or when you want a paragraph rather
    than structure. Cheaper than `recall_assessment` but less structured.
    """
    async with _client() as c:
        r = await c.post(
            "/recall",
            json={"query": query, "mode": "synthesis", "top_k": top_k},
        )
        r.raise_for_status()
        return r.json()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    mcp.run()


if __name__ == "__main__":
    main()
