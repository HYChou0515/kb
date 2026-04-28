"""Session domain struct — one OpenCode interactive session against a CaseStudy."""

from __future__ import annotations

from typing import Annotated

from autocrud import OnDelete, Ref
from msgspec import Struct

from rca.domain.types import SessionStatus


class Session(Struct):
    """One interactive OpenCode session against a CaseStudy.

    `workspace_path` mimics the v2 PV: a directory committed-back at session
    close. When a session is closed, transcript extraction creates GlossaryEntry,
    AgentFeedback, and DocumentSource records (linked back via session_id).
    """

    case_study_id: Annotated[str, Ref("case-study", on_delete=OnDelete.cascade)]
    status: SessionStatus = "active"
    opened_at: str = ""
    closed_at: str | None = None
    workspace_path: str = ""
    transcript_path: str | None = None
    rca_completed: bool = False
    notes: str = ""
