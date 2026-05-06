"""Session state persistence for rca_ui — single-user POC.

Each open case has:
  - <workspace>/session.json — metadata (status / opened_at / last_activity_at)
  - <workspace>/transcript.jsonl — append-only message log

There's at most ONE active session in this process at a time (matches
the single-user POC scope). The lock is enforced by `acquire_active`
and surfaces as `AnotherCaseActiveError` to UI callers; we mirror the
shape of the legacy kb-api workspace_lifecycle so a future rewire is
mechanical.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_SESSION_FILE = "session.json"
_TRANSCRIPT_FILE = "transcript.jsonl"


class AnotherCaseActiveError(RuntimeError):
    """Raised when caller tries to open case B while case A is still active."""


@dataclass
class SessionState:
    case_id: str
    status: str = "active"  # active | closed | finalized
    opened_at: str = ""
    last_activity_at: str = ""
    closed_at: str | None = None
    rca_completed: bool = False
    notes: str = ""

    @classmethod
    def fresh(cls, case_id: str) -> SessionState:
        now = _now_iso()
        return cls(case_id=case_id, opened_at=now, last_activity_at=now)


@dataclass
class _ActiveSession:
    case_id: str
    workspace: Path
    state: SessionState
    transcript_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


# Module-level single-active-session lock. POC scope is one user, so a
# process-local mutex is sufficient — multi-tenant deployment will need
# this scoped per-user (see design discussion).
_active_lock = asyncio.Lock()
_active: _ActiveSession | None = None


async def acquire_active(case_id: str, workspace: Path) -> _ActiveSession:
    """Take the active-session slot for `case_id`. If a different case is
    currently active, raise. Resuming the same case is a no-op return."""
    global _active
    async with _active_lock:
        if _active is not None and _active.case_id != case_id:
            raise AnotherCaseActiveError(
                f"Another case is already active: {_active.case_id}. "
                "Close it before opening a different case."
            )
        if _active is not None and _active.case_id == case_id:
            _active.state.last_activity_at = _now_iso()
            _save_state(_active.workspace, _active.state)
            return _active

        state = _load_or_init_state(workspace, case_id)
        state.status = "active"
        state.last_activity_at = _now_iso()
        _save_state(workspace, state)
        _active = _ActiveSession(case_id=case_id, workspace=workspace, state=state)
        return _active


async def release_active(
    case_id: str, *, status: str = "closed"
) -> SessionState | None:
    """Release the active slot if it matches `case_id`. Returns the final
    persisted state (or None if no matching active session)."""
    global _active
    async with _active_lock:
        if _active is None or _active.case_id != case_id:
            return None
        state = _active.state
        state.status = status
        state.closed_at = _now_iso()
        state.last_activity_at = state.closed_at
        _save_state(_active.workspace, state)
        _active = None
        return state


def get_active() -> _ActiveSession | None:
    return _active


def transcript_path(workspace: Path) -> Path:
    return workspace / _TRANSCRIPT_FILE


async def append_transcript(active: _ActiveSession, entry: dict[str, Any]) -> None:
    """Append one JSONL line under the per-session lock so concurrent
    streams don't interleave bytes."""
    entry = {**entry, "ts": entry.get("ts") or _now_iso()}
    async with active.transcript_lock:
        path = transcript_path(active.workspace)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        active.state.last_activity_at = entry["ts"]
        _save_state(active.workspace, active.state)


def read_transcript(workspace: Path) -> list[dict[str, Any]]:
    path = transcript_path(workspace)
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def read_transcript_text(workspace: Path) -> str:
    """Render transcript as plain text — used when posting to kb-api
    /retain at finalize time."""
    parts: list[str] = []
    for entry in read_transcript(workspace):
        role = entry.get("role", "?")
        content = entry.get("content", "")
        parts.append(f"## {role}\n\n{content}\n")
    return "\n".join(parts)


# ─── helpers ─────────────────────────────────────────────────────────────


def _load_or_init_state(workspace: Path, case_id: str) -> SessionState:
    path = workspace / _SESSION_FILE
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**raw)
    return SessionState.fresh(case_id)


def _save_state(workspace: Path, state: SessionState) -> None:
    path = workspace / _SESSION_FILE
    path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), "utf-8")


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()
