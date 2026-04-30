"""Manager-queue HTTP contract — verifies AutoCRUD's auto-generated
GET /rca-report endpoint already satisfies the manager signoff queue
without us needing a purpose-built /queue convenience endpoint.

Per the MCP-vs-web boundary (memory: feedback_mcp_vs_web_boundary), the
queue UX lives on the web/HTTP backend, not on MCP. Managers query this
endpoint from the web UI to see pending reports awaiting signoff.

If a test here fails because AutoCRUD's QB doesn't support what we need
(multi-field AND, ascending date sort, etc.), THAT'S the justification
for a thin /queue wrapper — until then we use the auto-generated routes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


class _NullGraph:
    """IGraphAdapter null-impl — manager queue tests don't exercise cognee.
    The mirror handler still fires on each AutoCRUD write but its calls go
    nowhere, which is what we want here (we're testing AutoCRUD, not mirror)."""

    async def setup(self) -> None:
        pass

    async def remember_text(self, *a: Any, **kw: Any) -> None:
        pass

    async def remember_files(self, *a: Any, **kw: Any) -> None:
        pass

    async def cognify(self, *a: Any, **kw: Any) -> None:
        pass

    async def recall(self, *a: Any, **kw: Any) -> list[Any]:
        return []

    async def forget(self) -> None:
        pass


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test-key")
    monkeypatch.setenv("AUTOCRUD_DATA_ROOT", str(tmp_path / "autocrud"))
    monkeypatch.setenv("COGNEE_DATA_ROOT", str(tmp_path / "cognee_data"))
    monkeypatch.setenv("COGNEE_SYSTEM_ROOT", str(tmp_path / "cognee_system"))
    monkeypatch.chdir(tmp_path)

    from rca.container import container
    from rca.main import app

    container.reset_singletons()
    container.graph.override(_NullGraph())

    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        container.graph.reset_override()
        container.reset_singletons()


def _create_case(client: TestClient) -> str:
    r = client.post("/case-study", json={"title": "t", "description": "d"})
    return r.json()["resource_id"]


def _create_session(client: TestClient, case_id: str) -> str:
    r = client.post(f"/session/open/{case_id}")
    return r.json()["resource_id"]


def _create_agreed_report(
    client: TestClient,
    case_id: str,
    session_id: str,
    *,
    agreed: bool = True,
    agreed_at: str | None = "2020-01-01T00:00:00Z",
) -> str:
    r = client.post(
        "/rca-report",
        json={
            "case_study_id": case_id,
            "session_id": session_id,
            "markdown_content": "# RCA",
            "agreed": agreed,
            "agreed_at": agreed_at,
            "signed_off_by": "alice",
        },
    )
    assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text}"
    return r.json()["resource_id"]


# ─── tracer bullet ─────────────────────────────────────────────────────────


def test_list_filtered_by_verification_status_returns_only_matching(
    app_client: TestClient,
) -> None:
    """Manager UX foundation: GET /rca-report with verification_status filter
    returns ONLY reports with that status. If this fails, AutoCRUD's QB
    doesn't honor the indexed_field on verification_status — and the manager
    queue requires either a thin convenience wrapper or fixing the QB call."""
    client = app_client
    case_id = _create_case(client)
    session_id = _create_session(client, case_id)

    # Two reports: one stays at default unverified, one gets signed.
    pending_id = _create_agreed_report(client, case_id, session_id)
    signed_id = _create_agreed_report(client, case_id, session_id)

    # Sign one as verified — manager workflow.
    sign_resp = client.post(
        f"/rca-report/{signed_id}/sign",
        json={
            "role": "manager",
            "status": "verified",
            "signed_by": "bob",
            "comment": "ok",
        },
    )
    assert sign_resp.status_code in (200, 201), (
        f"sign failed: {sign_resp.status_code} {sign_resp.text}"
    )

    # AutoCRUD's QB string expression — single field equality.
    # The web UI's manager queue panel builds an expression like this.
    r = client.get(
        "/rca-report",
        params={"qb": "QB['verification_status'].eq('unverified')"},
    )
    assert r.status_code == 200, f"list failed: {r.status_code} {r.text}"

    body = r.json()
    statuses = [item["data"].get("verification_status") for item in body]
    assert all(s == "unverified" for s in statuses), (
        f"QB filter for verification_status=unverified did NOT filter — "
        f"got statuses: {statuses}"
    )
    ids = _extract_ids(body)
    assert pending_id in ids, "pending report missing from filtered list"
    assert signed_id not in ids, "verified report leaked into unverified filter"


def test_combined_filter_unverified_and_agreed_excludes_drafts(
    app_client: TestClient,
) -> None:
    """Manager queue contract: pending reports = unverified + agreed.
    Drafts (agreed=False) are NOT in the manager's queue — they need author
    signoff first. Multiple data_conditions are AND'd by AutoCRUD."""
    client = app_client
    case_id = _create_case(client)
    session_id = _create_session(client, case_id)

    pending_id = _create_agreed_report(client, case_id, session_id, agreed=True)
    draft_id = _create_agreed_report(
        client, case_id, session_id, agreed=False, agreed_at=None
    )

    # AND-combine via QB's `&` operator on the expression string.
    qb = "QB['verification_status'].eq('unverified') & QB['agreed'].eq(True)"
    r = client.get("/rca-report", params={"qb": qb})
    assert r.status_code == 200, f"list failed: {r.status_code} {r.text}"

    ids = _extract_ids(r.json())
    assert pending_id in ids, "agreed unverified report should be in queue"
    assert draft_id not in ids, (
        f"draft (agreed=False) leaked into manager queue — AND filter broken. "
        f"ids returned: {ids}"
    )


def test_queue_sorted_by_agreed_at_oldest_first(app_client: TestClient) -> None:
    """Manager queue UX: the oldest pending report should appear first so
    backlogs surface visually. We sort by `agreed_at` ascending. If QB
    can't sort by agreed_at (e.g. it's not in indexed_fields), this test
    will RED — the fix is either adding agreed_at to indexed_fields or
    using AutoCRUD's built-in created_time as a proxy."""
    client = app_client
    case_id = _create_case(client)
    session_id = _create_session(client, case_id)

    # Create three reports in a deliberately scrambled chronological order
    # so neither insert order nor created_time accidentally matches
    # agreed_at order.
    middle_id = _create_agreed_report(
        client, case_id, session_id, agreed_at="2020-06-15T00:00:00Z"
    )
    oldest_id = _create_agreed_report(
        client, case_id, session_id, agreed_at="2020-01-01T00:00:00Z"
    )
    newest_id = _create_agreed_report(
        client, case_id, session_id, agreed_at="2020-12-31T00:00:00Z"
    )

    qb = "QB['verification_status'].eq('unverified').sort('+agreed_at')"
    r = client.get("/rca-report", params={"qb": qb})
    assert r.status_code == 200, f"list failed: {r.status_code} {r.text}"

    # The app instance is shared across pytest tests so the listing may
    # include records from other tests in the same run. Filter to OUR
    # three reports and assert their relative order.
    our_ids = {oldest_id, middle_id, newest_id}
    ids = [i for i in _extract_ids(r.json()) if i in our_ids]
    expected = [oldest_id, middle_id, newest_id]
    assert ids == expected, (
        f"queue not sorted by agreed_at ASC — expected {expected}, got {ids}"
    )


def _extract_ids(body: Any) -> list[str]:
    """Pull resource_id out of an AutoCRUD list response.

    Shape (verified empirically against the live app):
        [{"data": {...}, "revision_info": {"resource_id": "rca-report:UUID", ...}, ...}, ...]

    The id lives inside revision_info, not at the item top level."""
    items = body if isinstance(body, list) else []
    out: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rev = item.get("revision_info")
        if isinstance(rev, dict):
            rid = rev.get("resource_id")
            if isinstance(rid, str):
                out.append(rid)
    return out
