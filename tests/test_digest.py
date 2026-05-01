"""digest_session — unit tests.

Tests the session digest service which extracts conversation text and creates
a DocumentSource(conversation_extracted) record in AutoCRUD.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from rca.domain.case_study import CaseStudy
from rca.domain.session import Session


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
    """Provides live autocrud instance for digest tests."""
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


def _make_case(autocrud: Any) -> str:
    now = dt.datetime.now(dt.UTC)
    case = CaseStudy(title="Digest test case", description="test")
    return autocrud.case_study_mgr().create(case, user="test", now=now).resource_id


def _make_session(
    autocrud: Any, case_id: str, *, transcript_path: str | None = None
) -> str:
    now = dt.datetime.now(dt.UTC)
    sess = Session(
        case_study_id=case_id,
        status="closed",
        opened_at="2020-01-01T00:00:00Z",
        closed_at="2020-01-01T01:00:00Z",
        workspace_path="",
        transcript_path=transcript_path,
    )
    return autocrud.session_mgr().create(sess, user="test", now=now).resource_id


# ─── tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_digest_session_creates_document_source(
    autocrud_env: Any, tmp_path: Path
) -> None:
    """A session with a transcript creates a DocumentSource record and marks
    session.digested_at. This is the load-bearing test for the digest pipeline."""
    autocrud = autocrud_env

    # Write a fake transcript
    transcript_file = tmp_path / "transcript.json"
    transcript_file.write_text(
        '{"messages": [{"role": "user", "content": "Cu via resistance high"}]}',
        encoding="utf-8",
    )

    case_id = _make_case(autocrud)
    sess_id = _make_session(autocrud, case_id, transcript_path=str(transcript_file))

    from rca.services.digest import digest_session

    result = await digest_session(sess_id, autocrud=autocrud)
    assert result is True, "digest should return True when transcript processed"

    # Session should have digested_at set
    sess_resource = autocrud.session_mgr().get(sess_id)
    assert sess_resource.data.digested_at, "digested_at not set after digest"


@pytest.mark.asyncio
async def test_digest_session_skips_if_already_digested(
    autocrud_env: Any, tmp_path: Path
) -> None:
    """Calling digest_session twice returns False on the second call (dedup guard)."""
    autocrud = autocrud_env

    transcript_file = tmp_path / "t.json"
    transcript_file.write_text('{"messages": []}', encoding="utf-8")

    case_id = _make_case(autocrud)
    sess_id = _make_session(autocrud, case_id, transcript_path=str(transcript_file))

    from rca.services.digest import digest_session

    first = await digest_session(sess_id, autocrud=autocrud)
    second = await digest_session(sess_id, autocrud=autocrud)

    assert first is True
    assert second is False, "second digest call should be a no-op"


@pytest.mark.asyncio
async def test_digest_session_returns_false_when_no_transcript(
    autocrud_env: Any,
) -> None:
    """Session with no transcript_path → digest returns False (no document created)."""
    autocrud = autocrud_env

    case_id = _make_case(autocrud)
    sess_id = _make_session(autocrud, case_id, transcript_path=None)

    from rca.services.digest import digest_session

    result = await digest_session(sess_id, autocrud=autocrud)
    assert result is False
