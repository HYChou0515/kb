"""kb-mcp — stdio MCP server exposing 5 cognee primitives.

Tool names mirror the kb-api routes (remember / recall / search / improve /
forget). Used by external agents (Claude Desktop, Cursor, …) and by the
rca_ui agent's MCPServerStdio wiring.

Run:
    uv run kb-mcp                 # console script (stdio transport)
    uv run python -m rca.adapter.in_.mcp_kb
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import cognee
from cognee.modules.search.types import SearchType
from mcp.server.fastmcp import FastMCP

from rca.config import load_settings

logger = logging.getLogger(__name__)


_settings = load_settings()
_settings.export_to_cognee_env()


mcp = FastMCP("kb-mcp")


@mcp.tool()
async def remember(
    text: str,
    dataset_name: str = "main_dataset",
    session_id: str | None = None,
    self_improvement: bool = True,
    run_in_background: bool = False,
) -> dict[str, Any]:
    """Ingest text into the KB.

    `dataset_name` carries the trust-tier signal (e.g. "rca_reports" /
    "rca_literature" / "rca_conversations"). `self_improvement=True`
    triggers cognee's auto-improve pipeline after ingest.
    """
    result = await cognee.remember(
        text,
        dataset_name=dataset_name,
        session_id=session_id,
        self_improvement=self_improvement,
        run_in_background=run_in_background,
    )
    return _serialize(result)


@mcp.tool()
async def recall(
    query: str,
    datasets: list[str] | None = None,
    top_k: int = 10,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Session-aware retrieval. cognee.recall returns synthesized answers
    grounded in the graph context."""
    kwargs: dict[str, Any] = {}
    if session_id is not None:
        kwargs["session_id"] = session_id
    results = await cognee.recall(query, datasets=datasets, top_k=top_k, **kwargs)
    return {"results": _serialize(results)}


@mcp.tool()
async def search(
    query: str,
    query_type: str = "GRAPH_COMPLETION",
    datasets: list[str] | None = None,
    top_k: int = 10,
) -> dict[str, Any]:
    """General-purpose graph / vector search. `query_type` is a SearchType
    enum name (GRAPH_COMPLETION / CHUNKS / SUMMARIES / etc.)."""
    try:
        st = SearchType[query_type]
    except KeyError as exc:
        valid = sorted(t.name for t in SearchType)
        raise ValueError(f"Unknown query_type {query_type!r}. Valid: {valid}") from exc
    results = await cognee.search(
        query, query_type=st, datasets=datasets, top_k=top_k
    )
    return {"results": _serialize(results)}


@mcp.tool()
async def improve(
    dataset: str = "main_dataset",
    run_in_background: bool = False,
    session_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run cognee's improve pipeline (the v1 successor of cognify).
    Reprocesses a dataset, refreshing entities / relations / summaries."""
    result = await cognee.improve(
        dataset=dataset,
        run_in_background=run_in_background,
        session_ids=session_ids,
    )
    return _serialize(result) if result else {"status": "queued"}


@mcp.tool()
async def forget(
    data_id: str | None = None,
    dataset: str | None = None,
    everything: bool = False,
) -> dict[str, Any]:
    """Delete data. Pass exactly one of (data_id, dataset) or
    everything=True."""
    if not (data_id or dataset or everything):
        raise ValueError(
            "forget requires one of: data_id=<uuid> | dataset=<name|uuid> | everything=True"
        )
    parsed_data_id = UUID(data_id) if data_id else None
    parsed_dataset: str | UUID | None = dataset
    if dataset:
        try:
            parsed_dataset = UUID(dataset)
        except ValueError:
            parsed_dataset = dataset
    result = await cognee.forget(
        data_id=parsed_data_id, dataset=parsed_dataset, everything=everything
    )
    return _serialize(result) if isinstance(result, dict) else {"status": "ok"}


# ─── helpers ─────────────────────────────────────────────────────────────


def _serialize(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
