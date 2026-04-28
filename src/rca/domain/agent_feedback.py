"""AgentFeedback domain struct — where the agent was wrong/right vs the expert."""

from __future__ import annotations

from typing import Annotated

from autocrud import DisplayName, OnDelete, Ref
from msgspec import Struct

from rca.domain.types import FeedbackType


class AgentFeedback(Struct):
    """Where the agent's framing/vocabulary/reasoning was wrong or right
    vs. the expert. Used so future sessions can mirror the expert's language.
    """

    type: FeedbackType
    topic: Annotated[str, DisplayName()]
    agent_said: str
    expert_correction: str
    learning_for_agent: str
    source_session_id: Annotated[
        str | None, Ref("session", on_delete=OnDelete.set_null)
    ] = None
    source_case_study_id: Annotated[
        str | None, Ref("case-study", on_delete=OnDelete.set_null)
    ] = None
