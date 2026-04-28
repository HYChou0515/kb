"""GlossaryEntry domain struct — in-house abbreviation / jargon used by experts."""

from __future__ import annotations

from typing import Annotated

from autocrud import DisplayName, OnDelete, Ref
from msgspec import Struct

from rca.domain.types import GlossaryConfidence


class GlossaryEntry(Struct):
    """In-house abbreviation / jargon / internal codename used by the expert.

    Captured at session close from transcript extraction. Lookup pattern
    (e.g. "what does ABC123 mean?") goes through AutoCRUD QB; semantic
    pattern goes through cognee /recall.
    """

    term: Annotated[str, DisplayName()]
    expansion: str
    context: str
    confidence: GlossaryConfidence = "expert_implicit"
    source_session_id: Annotated[
        str | None, Ref("session", on_delete=OnDelete.set_null)
    ] = None
    source_case_study_id: Annotated[
        str | None, Ref("case-study", on_delete=OnDelete.set_null)
    ] = None
