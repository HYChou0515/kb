"""LocalSubprocessOpencodeRuntime — real `opencode serve` round trip.

E2E for the opencode runtime port. Spawns a real opencode subprocess
into an isolated XDG_DATA_HOME (so it doesn't pollute the user's own
opencode data), creates a session, asserts session_id round-trips,
deletes it. Tracer for the entire IOpencodeRuntime contract.

Skipped when:
  - opencode binary not on PATH
  - shutil.which("opencode") returns None

These tests do NOT need OPENAI_API_KEY (no LLM call — we never send a
prompt; just verify the session lifecycle endpoints work).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import AsyncIterator

import pytest
import pytest_asyncio

pytestmark = pytest.mark.integration


def _opencode_available() -> bool:
    return shutil.which("opencode") is not None


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def opencode_runtime(
    tmp_path_factory: pytest.TempPathFactory,
) -> AsyncIterator:
    """Session-scoped: spawn one opencode serve, share across tests in this
    file. Spawn cost (~1-2s) is amortized; each test creates its own session
    via the API and deletes it on the way out, so they don't interfere."""
    if not _opencode_available():
        pytest.skip("opencode binary not on PATH")

    from rca.adapter.out.opencode.local_subprocess import (
        LocalSubprocessOpencodeRuntime,
    )

    data_root = tmp_path_factory.mktemp("opencode_runtime_test")
    project_root = tmp_path_factory.mktemp("opencode_runtime_test_project")
    runtime = LocalSubprocessOpencodeRuntime(
        port=4097,  # avoid clashing with prod opencode on 4096
        opencode_data_root=data_root,
        config_content={"mcp": {}, "permission": {"edit": "ask", "bash": "ask"}},
    )
    # opencode pins its project root to the cwd at process start; create_session
    # would lazy-start it for us, but health_check / session_url tests don't go
    # through create_session, so we boot explicitly here.
    await runtime.start(cwd=project_root)
    try:
        yield runtime
    finally:
        await runtime.stop()


# ─── tracer ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_delete_session_round_trip(
    opencode_runtime, tmp_path: Path
) -> None:
    """Create a session pinned to a workspace dir, get back a non-empty
    session_id, delete it cleanly. Load-bearing for the whole user flow:
    if this fails, no opencode session lifecycle works end-to-end."""
    sess_id = await opencode_runtime.create_session(directory=tmp_path)

    assert sess_id, "create_session must return a non-empty session_id"

    # Idempotent: delete the same session twice (second should not raise)
    await opencode_runtime.delete_session(sess_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_health_check_when_running(opencode_runtime) -> None:
    """The runtime should report healthy after start() returns."""
    assert await opencode_runtime.health_check() is True


@pytest.mark.asyncio(loop_scope="session")
async def test_session_url_contains_session_id(opencode_runtime) -> None:
    """session_url is a pure URL builder — must include the session_id so
    the browser-side /app can scope to it."""
    fake_id = "ses_test_123"
    url = opencode_runtime.session_url(fake_id)
    assert fake_id in url
    assert url.startswith("http")


@pytest.mark.asyncio(loop_scope="session")
async def test_last_message_at_none_for_fresh_session(
    opencode_runtime, tmp_path: Path
) -> None:
    """A freshly-created session has no messages yet — None is the contract,
    not an exception, not a sentinel datetime."""
    sess_id = await opencode_runtime.create_session(directory=tmp_path)
    try:
        last = await opencode_runtime.last_message_at(sess_id)
        assert last is None, f"fresh session should have no last_message; got {last!r}"
    finally:
        await opencode_runtime.delete_session(sess_id)
