"""workspace_lifecycle — open_workspace() end-to-end tracer.

Goes through the real FastAPI app (TestClient) with:
  - IGraphAdapter overridden to a null impl (no cognee)
  - IOpencodeRuntime overridden to a fake (no real opencode process)

Verifies the full first-time open path:
  POST /case-study/{id}/open-workspace
    → workspace dir created on disk
    → CASE.md seeded with case title
    → Session record created with opencode_session_id
    → response includes session_id, opencode_session_id, opencode_url, resumed=False

Also covers:
  - 400 on closed CaseStudy
  - 404 on unknown case_id

NOTE on test setup: test cases are created via `container.autocrud()` directly (not
via the AutoCRUD HTTP route). This avoids the stale-routes problem: when multiple
TestClient fixtures run against the same global `app`, `autocrud.apply(app)` appends
routes each time. The first-registered AutoCRUD route wins for HTTP requests, and it
references the first test's AutoCrudWrapper. Using the container directly ensures both
case creation AND workspace opening go through the SAME AutoCrudWrapper instance.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from rca.domain.case_study import CaseStudy


class _NullGraph:
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


class _FakeOpencode:
    """Returns a deterministic session_id without spawning any process."""

    async def health_check(self) -> bool:
        return True

    async def create_session(self, *, directory: Path) -> str:
        return f"sess_fake_{directory.name[:8]}"

    async def delete_session(self, opencode_session_id: str) -> None:
        pass

    async def last_message_at(self, opencode_session_id: str) -> dt.datetime | None:
        return None

    def session_url(self, opencode_session_id: str) -> str:
        return f"http://fake-opencode/app?session={opencode_session_id}"


@pytest.fixture
def app_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """TestClient + the live autocrud instance.

    Yields (TestClient, autocrud) so tests can create records via container.autocrud()
    directly — bypassing the AutoCRUD HTTP routes and avoiding the stale-route
    problem (multiple TestClient runs against the same global `app`).
    """
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
    container.opencode.override(_FakeOpencode())

    try:
        with TestClient(app) as c:
            yield c, container.autocrud()
    finally:
        container.graph.reset_override()
        container.opencode.reset_override()
        container.reset_singletons()


def _make_case(autocrud: Any, *, title: str = "Cu via resistance spike", status: str = "active") -> str:
    """Create a CaseStudy directly via the AutoCRUD manager. Returns resource_id."""
    now = dt.datetime.now(dt.UTC)
    case = CaseStudy(title=title, description="yield drop", status=status)  # type: ignore[arg-type]
    rev = autocrud.case_study_mgr().create(case, user="test", now=now)
    return rev.resource_id


# ─── tracer ─────────────────────────────────────────────────────────────────


def test_open_workspace_first_time_seeds_dir_and_returns_opencode_url(
    app_env: tuple,
) -> None:
    """First-time open: workspace seeded with template + CASE.md rendered from
    CaseStudy, Session record created with opencode_session_id. This is the
    load-bearing test for the entire workspace+opencode open flow."""
    client, autocrud = app_env
    case_id = _make_case(autocrud, title="Cu via resistance spike")

    r = client.post(f"/case-study/{case_id}/open-workspace")
    assert r.status_code == 200, f"open-workspace failed: {r.status_code} {r.text}"

    body = r.json()
    assert body.get("session_id"), "session_id missing"
    assert body.get("opencode_session_id"), "opencode_session_id missing"
    assert body.get("opencode_url", "").startswith("http"), "opencode_url not a URL"
    assert body.get("resumed") is False, "first-time open should not be resumed"

    workspace = Path(body["workspace_path"])
    assert workspace.is_dir(), f"workspace dir not created: {workspace}"
    case_md = (workspace / "CASE.md").read_text()
    assert "Cu via resistance spike" in case_md, "CASE.md missing case title"

    # Template files should also be seeded
    assert (workspace / "AGENTS.md").exists(), "AGENTS.md not seeded"


def test_open_workspace_closed_case_returns_400(
    app_env: tuple,
) -> None:
    """CaseStudy in closed status must be rejected — user must PATCH back to
    active before reopening. 400 is the contract."""
    client, autocrud = app_env
    case_id = _make_case(autocrud, status="closed")

    r = client.post(f"/case-study/{case_id}/open-workspace")
    assert r.status_code == 400, (
        f"expected 400 for closed case, got {r.status_code}: {r.text}"
    )


def test_open_workspace_unknown_case_returns_404(
    app_env: tuple,
) -> None:
    """Non-existent case_id → 404 (AutoCRUD ResourceIDNotFoundError propagated)."""
    client, _ = app_env
    r = client.post("/case-study/nonexistent-id/open-workspace")
    assert r.status_code == 404, (
        f"expected 404 for unknown case, got {r.status_code}: {r.text}"
    )


def test_open_workspace_session_record_has_opencode_fields(
    app_env: tuple,
) -> None:
    """The Session record created by open-workspace must carry opencode_session_id
    and opencode_url so the watchdog and resume path can find them."""
    client, autocrud = app_env
    case_id = _make_case(autocrud)

    r = client.post(f"/case-study/{case_id}/open-workspace")
    assert r.status_code == 200
    body = r.json()
    sess_id = body["session_id"]

    # Verify the session record via the same autocrud instance that created it.
    # Using the HTTP GET /session/{id} would hit a stale AutoCRUD route from an
    # earlier test's lifespan, which doesn't know about this session.
    session_resource = autocrud.session_mgr().get(sess_id)
    sess_data = session_resource.data

    assert sess_data.opencode_session_id == body["opencode_session_id"]
    assert sess_data.opencode_url == body["opencode_url"]
    assert sess_data.status == "active"
