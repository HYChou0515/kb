"""Sign-report HTTP flow — verifies AutoCRUD-mounted /sign endpoint works
end-to-end: POST /rca-report (create) → POST /rca-report/{id}/sign → GET to
confirm verification fields persisted.

Uses real AutoCrudWrapper backed by tmp_path; only the graph adapter is
faked (no real cognee). The cognee mirror handler still fires on each
write — it just calls the fake graph, so we can also assert on what the
mirror saw.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


class _RecordingGraph:
    """GraphClient fake that records every add_text() call so we can assert
    the cognee mirror mirrored the right node_set tags after /sign."""

    def __init__(self) -> None:
        self.adds: list[tuple[str, list[str]]] = []  # (text, node_set) pairs

    async def setup(self) -> None: pass

    async def add_text(
        self, text: str, *, dataset: str = "rca", node_set: list[str] | None = None
    ) -> None:
        self.adds.append((text, node_set or []))

    async def add_documents(self, *a: Any, **kw: Any) -> None: pass
    async def cognify(self, *a: Any, **kw: Any) -> None: pass
    async def search(self, *a: Any, **kw: Any) -> list[Any]: return []
    async def prune(self) -> None: pass


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test-key")
    monkeypatch.setenv("AUTOCRUD_DATA_ROOT", str(tmp_path / "autocrud"))
    monkeypatch.setenv("COGNEE_DATA_ROOT", str(tmp_path / "cognee_data"))
    monkeypatch.setenv("COGNEE_SYSTEM_ROOT", str(tmp_path / "cognee_system"))
    monkeypatch.chdir(tmp_path)

    from rca.main import app, container

    container.reset_singletons()
    fake_graph = _RecordingGraph()
    container.graph.override(fake_graph)

    try:
        # raise_server_exceptions=False so 4xx/5xx come back as Response objects
        # rather than re-raising ValueError into the test (action raises
        # ValueError on policy violations; we want to assert on status_code).
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, fake_graph
    finally:
        container.graph.reset_override()
        container.reset_singletons()


def _create_case(client: TestClient) -> str:
    r = client.post("/case-study", json={"title": "t", "description": "d"})
    return r.json()["resource_id"]


def _create_session(client: TestClient, case_id: str) -> str:
    r = client.post(f"/session/open/{case_id}")
    return r.json()["resource_id"]


def _create_agreed_report(client: TestClient, case_id: str, session_id: str) -> str:
    """POST /rca-report with agreed=True → returns resource_id."""
    r = client.post(
        "/rca-report",
        json={
            "case_study_id": case_id,
            "session_id": session_id,
            "markdown_content": "# RCA\n真因: CMP slurry pH drift",
            "agreed": True,
            "agreed_at": "2020-01-01T00:00:00Z",
            "signed_off_by": "alice",
        },
    )
    assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text}"
    return r.json()["resource_id"]


def test_sign_report_persists_verification_status(app_client) -> None:
    """POST /rca-report/{id}/sign → record's verification_status changes from
    'unverified' (default) to 'verified', verified_by + verifier_role + comment
    + signoff_turnaround_seconds populated. GET confirms persistence."""
    client, _ = app_client
    case_id = _create_case(client)
    session_id = _create_session(client, case_id)
    report_id = _create_agreed_report(client, case_id, session_id)

    # Default state: unverified
    r0 = client.get(f"/rca-report/{report_id}")
    assert r0.json()["data"]["verification_status"] == "unverified"

    # Manager signs as verified
    r_sign = client.post(
        f"/rca-report/{report_id}/sign",
        json={
            "role": "manager",
            "status": "verified",
            "signed_by": "bob",
            "comment": "reviewed at design review",
        },
    )
    assert r_sign.status_code in (200, 201), (
        f"sign failed: {r_sign.status_code} {r_sign.text}"
    )

    # Re-fetch and assert all verification fields
    r1 = client.get(f"/rca-report/{report_id}")
    data = r1.json()["data"]
    assert data["verification_status"] == "verified"
    assert data["verifier_role"] == "manager"
    assert data["verified_by"] == "bob"
    assert data["signoff_comment"] == "reviewed at design review"
    assert data["verified_at"] is not None
    assert data["signoff_turnaround_seconds"] is not None
    assert data["signoff_turnaround_seconds"] >= 0


# NOTE: The HTTP-level mirror integration test was intentionally dropped.
# CogneeMirrorHandler.handle_event uses `loop.create_task(...)` (fire-and-
# forget) so the mirror's GraphClient.add_text call may not have completed
# by the time the sync test thread checks fake_graph.adds. The renderer's
# 4-tier node_set behavior is covered deterministically at unit level by
# tests/test_cognee_mirror.py::test_mirror_status_aware_node_set.


def test_sign_rejects_invalid_role_status_combo(app_client) -> None:
    """The /sign action validates role/status enforcement at the HTTP layer:
    author cannot self-elevate to verified."""
    client, _ = app_client
    case_id = _create_case(client)
    session_id = _create_session(client, case_id)
    report_id = _create_agreed_report(client, case_id, session_id)

    r = client.post(
        f"/rca-report/{report_id}/sign",
        json={"role": "author", "status": "verified", "signed_by": "alice"},
    )
    # Surfaced as 4xx or 5xx — the action raised ValueError, KB API's
    # exception_handler maps it to JSON error.
    assert r.status_code >= 400, f"expected error, got {r.status_code}: {r.text}"
    assert "cannot set status" in r.text.lower(), (
        f"expected role/status policy in error, got: {r.text}"
    )

    # Status unchanged (still unverified)
    r_get = client.get(f"/rca-report/{report_id}")
    assert r_get.json()["data"]["verification_status"] == "unverified"
