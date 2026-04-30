"""stale_notify — stale-case detection and notification tests."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from rca.domain.case_study import CaseStudy
from rca.domain.rca_report import RCAReport


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


@pytest.fixture
def autocrud_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
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
        with TestClient(app):
            yield container.autocrud()
    finally:
        container.graph.reset_override()
        container.reset_singletons()


@pytest.fixture
def app_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
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
        with TestClient(app) as c:
            yield c, container.autocrud()
    finally:
        container.graph.reset_override()
        container.reset_singletons()


# ─── helpers ─────────────────────────────────────────────────────────────────


def _make_old_case(autocrud: Any, *, title: str = "Old case", days_ago: int = 8) -> str:
    old_time = dt.datetime.now(dt.UTC) - dt.timedelta(days=days_ago)
    case = CaseStudy(title=title, description="test")
    return autocrud.case_study_mgr().create(case, user="test", now=old_time).resource_id


def _make_recent_case(autocrud: Any, *, title: str = "Recent case") -> str:
    now = dt.datetime.now(dt.UTC)
    case = CaseStudy(title=title, description="test")
    return autocrud.case_study_mgr().create(case, user="test", now=now).resource_id


def _make_agreed_report(autocrud: Any, case_id: str) -> None:
    now = dt.datetime.now(dt.UTC)
    report = RCAReport(
        case_study_id=case_id,
        session_id="sess_fake",
        agreed=True,
        agreed_at=now.isoformat(),
        markdown_content="# Report",
    )
    autocrud.rca_report_mgr().create(report, user="test", now=now)


# ─── find_stale_cases ─────────────────────────────────────────────────────────


def test_find_stale_cases_returns_old_active_cases_without_report(
    autocrud_env: Any,
) -> None:
    """An active case older than stale_days with no agreed report is stale."""
    autocrud = autocrud_env
    case_id = _make_old_case(autocrud, title="Old no report")

    from rca.services.stale_notify import find_stale_cases

    stale = find_stale_cases(autocrud, stale_days=7)
    assert any(s.case_id == case_id for s in stale)


def test_find_stale_cases_excludes_case_with_agreed_report(
    autocrud_env: Any,
) -> None:
    """A case with an agreed RCAReport is not stale even if old."""
    autocrud = autocrud_env
    case_id = _make_old_case(autocrud, title="Old with report")
    _make_agreed_report(autocrud, case_id)

    from rca.services.stale_notify import find_stale_cases

    stale = find_stale_cases(autocrud, stale_days=7)
    assert not any(s.case_id == case_id for s in stale)


def test_find_stale_cases_excludes_recent_case(
    autocrud_env: Any,
) -> None:
    """A case created today is not stale even without a report."""
    autocrud = autocrud_env
    case_id = _make_recent_case(autocrud)

    from rca.services.stale_notify import find_stale_cases

    stale = find_stale_cases(autocrud, stale_days=7)
    assert not any(s.case_id == case_id for s in stale)


# ─── notify_stale_cases ───────────────────────────────────────────────────────


def test_notify_stale_cases_logs_and_updates_notify_at(
    autocrud_env: Any,
) -> None:
    """notify_stale_cases returns 1 and sets last_stale_notify_at on the case."""
    autocrud = autocrud_env
    case_id = _make_old_case(autocrud)

    from rca.services.stale_notify import notify_stale_cases

    count = notify_stale_cases(autocrud, stale_days=7, notify_interval_days=3)
    assert count == 1

    case_resource = autocrud.case_study_mgr().get(case_id)
    assert case_resource.data.last_stale_notify_at is not None


def test_notify_stale_cases_respects_interval(
    autocrud_env: Any,
) -> None:
    """A case notified 1 day ago is skipped (3-day interval not elapsed)."""
    autocrud = autocrud_env
    recent_notify = (dt.datetime.now(dt.UTC) - dt.timedelta(days=1)).isoformat()
    old_time = dt.datetime.now(dt.UTC) - dt.timedelta(days=8)
    case = CaseStudy(
        title="Recently notified", description="x", last_stale_notify_at=recent_notify
    )
    autocrud.case_study_mgr().create(case, user="test", now=old_time)

    from rca.services.stale_notify import notify_stale_cases

    count = notify_stale_cases(autocrud, stale_days=7, notify_interval_days=3)
    assert count == 0


# ─── HTTP endpoints ───────────────────────────────────────────────────────────


def test_get_admin_stale_cases_endpoint(app_env: tuple) -> None:
    """GET /admin/stale-cases lists stale cases with case_id, title, created_time."""
    client, autocrud = app_env
    case_id = _make_old_case(autocrud, title="Old stale case")

    r = client.get("/admin/stale-cases")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert isinstance(body, list)
    assert any(item["case_id"] == case_id for item in body)
    item = next(x for x in body if x["case_id"] == case_id)
    assert item["title"] == "Old stale case"
    assert "created_time" in item


def test_post_admin_notify_stale_cases_endpoint(app_env: tuple) -> None:
    """POST /admin/notify-stale-cases triggers notifications and returns count."""
    client, autocrud = app_env
    _make_old_case(autocrud, title="Notify trigger case")

    r = client.post("/admin/notify-stale-cases")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert body["notified"] >= 1
