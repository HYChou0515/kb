"""Session domain struct — one OpenCode interactive session against a CaseStudy."""

from __future__ import annotations

from typing import Annotated, Literal

from autocrud import OnDelete, Ref
from msgspec import Struct

from rca.domain.types import SessionStatus


InactivityCloseReason = Literal[
    "user_left",
    "watchdog_timeout",
    "explicit_close",
    "finalize",
]


class Session(Struct):
    """One interactive OpenCode session against a CaseStudy.

    `workspace_path` mimics the v2 PV: a directory committed-back at session
    close. When a session is closed, transcript extraction creates GlossaryEntry,
    AgentFeedback, and DocumentSource records (linked back via session_id).

    `opencode_session_id` lets resume reuse the same opencode-side session
    (chat history persisted in opencode's SQLite) — the RCA Session record
    is a thin wrapper that points at it. `last_activity_at` drives the
    inactivity watchdog; `digested_at` prevents re-digesting on second
    close events.
    """

    case_study_id: Annotated[str, Ref("case-study", on_delete=OnDelete.cascade)]
    status: SessionStatus = "active"
    opened_at: str = ""
    closed_at: str | None = None
    workspace_path: str = ""
    transcript_path: str | None = None
    rca_completed: bool = False
    notes: str = ""

    opencode_session_id: str | None = None
    opencode_url: str | None = None
    last_activity_at: str | None = None
    digested_at: str | None = None
    inactivity_close_reason: InactivityCloseReason | None = None
