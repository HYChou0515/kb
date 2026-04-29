"""Session lifecycle integration — open / close / abandon via HTTP.

Goes through FastAPI TestClient so AutoCRUD's per-request context
(now_ctx, user_ctx) is set up naturally. The full path exercised:
  HTTP → AutoCRUD-generated route → action factory closure →
  case_study_mgr().get/update + filesystem tar/untar.

We override the graph adapter only (avoid real cognee setup) — autocrud
runs against tmp_path on disk, so the test verifies the actual workspace
commit/restore lifecycle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


class _FakeGraph:
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
    """TestClient against the real app, with graph overridden to a fake.
    KBService stays real (so AutoCRUD-generated routes wire correctly)."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test-key")
    monkeypatch.setenv("AUTOCRUD_DATA_ROOT", str(tmp_path / "autocrud"))
    monkeypatch.setenv("COGNEE_DATA_ROOT", str(tmp_path / "cognee_data"))
    monkeypatch.setenv("COGNEE_SYSTEM_ROOT", str(tmp_path / "cognee_system"))
    # Redirect PROJECT_ROOT-derived dirs (active_sessions/, transcripts/)
    # so we don't pollute repo root during tests.
    monkeypatch.chdir(tmp_path)

    from rca.container import container
    from rca.main import app

    container.reset_singletons()
    container.graph.override(_FakeGraph())

    try:
        with TestClient(app) as c:
            yield c
    finally:
        container.graph.reset_override()
        container.reset_singletons()


def _create_case(client: TestClient) -> str:
    """POST /case-study → resource_id."""
    r = client.post("/case-study", json={"title": "t1", "description": "test case"})
    assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text}"
    return r.json()["resource_id"]


def _open_session(client: TestClient, case_id: str) -> tuple[str, dict]:
    """POST /session/open/{case_id} then GET to fetch data. Returns (id, data)."""
    r_open = client.post(f"/session/open/{case_id}")
    assert r_open.status_code in (200, 201), (
        f"open failed: {r_open.status_code} {r_open.text}"
    )
    sess_id = r_open.json()["resource_id"]

    r_get = client.get(f"/session/{sess_id}")
    assert r_get.status_code == 200, f"get failed: {r_get.status_code}"
    return sess_id, r_get.json()["data"]


def test_session_open_creates_active_workspace(app_client: TestClient) -> None:
    """POST /session/open/{case_id} runs the open_session action factory:
    fresh active workspace dir created on disk under active_sessions/."""
    case_id = _create_case(app_client)
    _, sess_data = _open_session(app_client, case_id)

    assert sess_data["status"] == "active"
    workspace = sess_data["workspace_path"]
    assert workspace, "workspace_path missing"
    assert Path(workspace).is_dir(), "active workspace dir not created"
    assert sess_data["case_study_id"] == case_id


def test_session_close_tarballs_workspace(app_client: TestClient) -> None:
    """close_session: tar the active dir → CaseStudy.workspace_archive (new
    revision), tear down the active dir."""
    case_id = _create_case(app_client)
    sess_id, sess_data = _open_session(app_client, case_id)
    workspace = Path(sess_data["workspace_path"])

    # drop files so the tarball is non-empty
    (workspace / "notes.md").write_text("hello", encoding="utf-8")

    r_close = app_client.post(f"/session/{sess_id}/close-session")
    assert r_close.status_code in (200, 201), (
        f"close failed: {r_close.status_code} {r_close.text}"
    )
    assert not workspace.exists(), "active dir should be torn down"

    # Fetch session and case-study data
    r_sess = app_client.get(f"/session/{sess_id}")
    assert r_sess.json()["data"]["status"] == "closed"

    r_case = app_client.get(f"/case-study/{case_id}")
    assert r_case.json()["data"]["workspace_archive"] is not None, (
        "archive not committed"
    )


def test_session_abandon_drops_workspace(app_client: TestClient) -> None:
    """abandon_session destroys the active dir without committing.
    CaseStudy.workspace_archive stays at its previous (None) value."""
    case_id = _create_case(app_client)
    sess_id, sess_data = _open_session(app_client, case_id)
    workspace = Path(sess_data["workspace_path"])

    r_abandon = app_client.post(f"/session/{sess_id}/abandon-session")
    assert r_abandon.status_code in (200, 201), (
        f"abandon failed: {r_abandon.status_code} {r_abandon.text}"
    )
    assert not workspace.exists(), "active dir should be removed"

    r_sess = app_client.get(f"/session/{sess_id}")
    assert r_sess.json()["data"]["status"] == "abandoned"

    # CaseStudy untouched
    r_case = app_client.get(f"/case-study/{case_id}")
    assert r_case.json()["data"]["workspace_archive"] is None
