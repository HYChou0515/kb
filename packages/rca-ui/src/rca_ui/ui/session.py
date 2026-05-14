"""Per-browser session bookkeeping for the UI layer.

Each browser gets a stable UUID via `app.storage.browser` (cookie-
backed, signed by `RCA_UI_STORAGE_SECRET`).  Every per-user resource —
workspace dir, AgentRuntime, MCP filesystem sandbox root — is scoped
under that UUID so two concurrent users on the same server never see
each other's data.

This module exposes:
- `current_session_id()` — read/seed the browser's UUID
- `current_session_root(settings)` — workspace root for that session
- `_runtimes` — process-wide registry mapping session_id → AgentRuntime
"""

from __future__ import annotations

import uuid
from pathlib import Path

from nicegui import app

from rca_ui.agent import AgentRuntime
from rca_ui.config import UISettings

_SESSION_KEY = "session_id"

# Process-wide registry of per-session runtimes.  AgentRuntime owns
# long-lived MCP subprocesses, so we lazy-spawn on the user's first
# message and keep it warm for the rest of their session.  Keyed by
# session_id.  Access via `_runtimes[sid]` from `case_chat`.
_runtimes: dict[str, AgentRuntime] = {}


def current_session_id() -> str:
    """Return this browser's session UUID, generating one on first
    call and persisting it to the signed browser-cookie storage."""
    sid = app.storage.browser.get(_SESSION_KEY)
    if not sid:
        sid = uuid.uuid4().hex
        app.storage.browser[_SESSION_KEY] = sid
    return sid


def current_session_root(settings: UISettings) -> Path:
    """Workspace root for the current browser session.  Cases live as
    `<workspace_root>/<session_id>/<case_id>/`.  The directory is
    created on demand."""
    root = settings.workspace_root / current_session_id()
    root.mkdir(parents=True, exist_ok=True)
    return root
