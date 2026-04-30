"""Outbound port to a running opencode server.

Architecture C: one shared opencode `serve` process hosts many sessions
(one per RCA Session). This port hides whether the process is local
(LocalSubprocessOpencodeRuntime — POC, spawns a child process) or remote
(future RemoteOpencodeRuntime — pod, talks to a separately-deployed
opencode service over the cluster network).

Both impls implement the same surface, so the swap is configuration-only.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from pathlib import Path


class IOpencodeRuntime(ABC):
    """Connection to a running opencode server.

    Lifecycle methods (start/stop) live on the concrete impl, not the
    port — RemoteOpencodeRuntime has nothing to start. The port itself
    is the data-plane: create/delete/inspect sessions hosted by the server.
    """

    @abstractmethod
    async def health_check(self) -> bool:
        """True iff the opencode server's /global/health responds 2xx."""
        ...

    @abstractmethod
    async def create_session(self, *, directory: Path) -> str:
        """POST /session — create a new opencode session pinned to the
        given working directory. Returns the opencode session_id, which
        we store on the RCA Session record (`opencode_session_id`)."""
        ...

    @abstractmethod
    async def delete_session(self, opencode_session_id: str) -> None:
        """DELETE /session/<id> — drop the session permanently. Used by
        finalize (hard close); soft close keeps the session in opencode's
        SQLite for resume."""
        ...

    @abstractmethod
    async def last_message_at(self, opencode_session_id: str) -> dt.datetime | None:
        """Latest message timestamp on the session (user OR agent reply).
        None if session has no messages or doesn't exist. Drives the
        inactivity watchdog."""
        ...

    @abstractmethod
    def session_url(self, opencode_session_id: str) -> str:
        """Browser-facing URL for this session. User opens this in their
        browser; opencode's /app loads the chat UI scoped to the given
        session_id. Pure function (URL build), not async."""
        ...
