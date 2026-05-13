"""Transcript I/O for the RCA case workspace.

Each case has `<workspace>/transcript.jsonl` — an append-only log of
user / assistant turns rendered by the UI.

Multi-user / multi-tab: workspaces are scoped per browser session by the
UI (workspace_root / session_id / case_id), so cross-user collisions are
prevented at the path level — this module just needs to keep concurrent
appends *within* one workspace from interleaving bytes. A per-workspace
asyncio.Lock does that.

The previous "single-active-case" mutex and `session.json` bookkeeping
have been removed: multi-user concurrency is handled by per-session
runtimes, and we don't need a process-wide active flag any more.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from pathlib import Path
from typing import Any

_TRANSCRIPT_FILE = "transcript.jsonl"

# Per-workspace asyncio.Lock; protects only against interleaved bytes on
# concurrent append within the same workspace.  Cleared lazily — entries
# stick around for the process lifetime but are cheap (an empty Lock).
_locks: dict[Path, asyncio.Lock] = {}


def transcript_path(workspace: Path) -> Path:
    return workspace / _TRANSCRIPT_FILE


def _lock_for(workspace: Path) -> asyncio.Lock:
    key = workspace.resolve()
    lock = _locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _locks[key] = lock
    return lock


async def append_transcript(workspace: Path, entry: dict[str, Any]) -> None:
    """Append one JSONL line to the workspace transcript. Held under a
    per-workspace asyncio lock so concurrent streams don't interleave
    bytes on the same file."""
    entry = {**entry, "ts": entry.get("ts") or _now_iso()}
    async with _lock_for(workspace):
        path = transcript_path(workspace)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


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
    """Render transcript as plain text — used when feeding the
    transcript back into the KB as a digested conversation record."""
    parts: list[str] = []
    for entry in read_transcript(workspace):
        role = entry.get("role", "?")
        content = entry.get("content", "")
        parts.append(f"## {role}\n\n{content}\n")
    return "\n".join(parts)


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()
