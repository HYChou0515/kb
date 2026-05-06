"""Thin HTTP client to kb-api (5 routes + health).

kb-api is a cognee proxy now — it has no typed records and no case CRUD.
The UI never asks kb-api about cases; case state is on disk under
data/workspaces/<case_id>/. The client only does:

    remember(text, dataset_name, …)
    recall(query, …)
    search(query, query_type, …)
    improve(dataset, …)
    forget(data_id | dataset | everything)

Used by the UI's "Submit final report" button (POST /remember with
dataset_name="rca_reports") and "Digest transcript on close" hook
(POST /remember with dataset_name="rca_conversations"). The agent
itself talks to kb-mcp directly (stdio), not through this client.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class KBClient:
    def __init__(self, base_url: str, *, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def health(self) -> bool:
        try:
            r = await self._client.get("/health")
            return r.status_code < 300
        except httpx.RequestError:
            return False

    # ─── primary API ──────────────────────────────────────────────────

    async def remember(
        self,
        *,
        text: str | list[str],
        dataset_name: str = "main_dataset",
        session_id: str | None = None,
        self_improvement: bool = True,
        run_in_background: bool = False,
        label: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "text": text,
            "dataset_name": dataset_name,
            "self_improvement": self_improvement,
            "run_in_background": run_in_background,
        }
        if session_id is not None:
            payload["session_id"] = session_id
        if label is not None:
            payload["label"] = label
        r = await self._client.post("/remember", json=payload)
        r.raise_for_status()
        return r.json()

    async def recall(
        self,
        *,
        query: str,
        datasets: list[str] | None = None,
        top_k: int = 10,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query, "top_k": top_k}
        if datasets:
            payload["datasets"] = datasets
        if session_id:
            payload["session_id"] = session_id
        r = await self._client.post("/recall", json=payload)
        r.raise_for_status()
        return r.json()

    async def search(
        self,
        *,
        query: str,
        query_type: str = "GRAPH_COMPLETION",
        datasets: list[str] | None = None,
        top_k: int = 10,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query,
            "query_type": query_type,
            "top_k": top_k,
        }
        if datasets:
            payload["datasets"] = datasets
        r = await self._client.post("/search", json=payload)
        r.raise_for_status()
        return r.json()

    async def improve(
        self,
        *,
        dataset: str = "main_dataset",
        run_in_background: bool = False,
        session_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset": dataset,
            "run_in_background": run_in_background,
        }
        if session_ids:
            payload["session_ids"] = session_ids
        r = await self._client.post("/improve", json=payload)
        r.raise_for_status()
        return r.json()

    async def forget(
        self,
        *,
        data_id: str | None = None,
        dataset: str | None = None,
        everything: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if data_id is not None:
            params["data_id"] = data_id
        if dataset is not None:
            params["dataset"] = dataset
        if everything:
            params["everything"] = "true"
        r = await self._client.delete("/forget", params=params)
        r.raise_for_status()
        return r.json()
