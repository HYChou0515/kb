"""Thin HTTP client to kb-api.

rca_ui needs three things from kb-api:

  - GET /case-study/<id>  — fetch CaseStudy metadata to render CASE.md
  - POST /retain/text     — ingest the agreed-final RCA report (the agent
                            also has kb-mcp.retain_text but we expose a
                            UI-driven path for "submit final" button)
  - POST /retain/conversation — ingest transcript at session close

Kept deliberately small — the bulk of kb interaction happens via kb-mcp
(stdio) inside the agent loop.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class KBClient:
    def __init__(self, base_url: str, *, timeout: float = 15.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    # ─── reads ────────────────────────────────────────────────────────

    async def get_case(self, case_id: str) -> dict[str, Any]:
        """Fetch a CaseStudy. AutoCRUD response is `{data, revision_info}`;
        we flatten so callers get one dict with `id` filled in."""
        r = await self._client.get(f"/case-study/{case_id}")
        r.raise_for_status()
        return _flatten(r.json())

    async def list_cases(self) -> list[dict[str, Any]]:
        r = await self._client.get("/case-study")
        r.raise_for_status()
        body = r.json()
        items = body if isinstance(body, list) else (
            body.get("items") or body.get("data") or []
        )
        return [_flatten(it) for it in items if isinstance(it, dict)]

    # ─── writes ───────────────────────────────────────────────────────

    async def retain_report(
        self,
        *,
        text: str,
        label: str,
        case_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /retain/text with source_kind=rca_report (highest trust tier).
        Used when the user clicks "submit final" in the UI."""
        return await self._retain(
            text=text,
            label=label,
            source_kind="rca_report",
            case_study_id=case_id,
        )

    async def retain_conversation(
        self,
        *,
        text: str,
        label: str,
        case_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._retain(
            text=text,
            label=label,
            source_kind="conversation",
            case_study_id=case_id,
        )

    async def _retain(
        self,
        *,
        text: str,
        label: str,
        source_kind: str,
        case_study_id: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "text": text,
            "label": label,
            "source_kind": source_kind,
            "cognify": True,
        }
        if case_study_id:
            payload["case_study_id"] = case_study_id
        r = await self._client.post("/retain/text", json=payload)
        r.raise_for_status()
        return r.json()


def _flatten(item: dict[str, Any]) -> dict[str, Any]:
    """AutoCRUD returns `{data: {...}, revision_info: {resource_id, ...}}`.
    Merge into a single dict with `id` for caller ergonomics."""
    data = dict(item.get("data") or {})
    rev = item.get("revision_info") or {}
    rid = rev.get("resource_id") or item.get("id") or item.get("resource_id")
    if rid:
        data["id"] = rid
    return data
