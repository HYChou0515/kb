"""DocumentSource domain struct — any document whose full text is ingested."""

from __future__ import annotations

from typing import Annotated

from autocrud import DisplayName, OnDelete, Ref
from msgspec import Struct

from rca.domain.types import DocumentKind


class DocumentSource(Struct):
    """Any document whose full text is ingested into cognee for retrieval.

    AutoCRUD stores the metadata + full text (audit, search, version);
    cognee gets a rendered chunk via the mirror event handler.
    """

    label: Annotated[str, DisplayName()]
    source_kind: DocumentKind
    text: str
    case_study_id: Annotated[
        str | None, Ref("case-study", on_delete=OnDelete.set_null)
    ] = None
    session_id: Annotated[str | None, Ref("session", on_delete=OnDelete.set_null)] = (
        None
    )
