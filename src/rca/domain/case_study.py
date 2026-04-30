"""CaseStudy domain struct — one defect case under investigation."""

from __future__ import annotations

from typing import Annotated

from autocrud import DisplayName
from autocrud.types import Binary
from msgspec import Struct

from rca.domain.types import CaseStatus


class CaseStudy(Struct):
    """A defect case under investigation. Container for one or many Sessions.

    `workspace_archive` is a tar.gz of the case's persistent state (agent
    notes, draft reports, etc.) — committed at session close, restored at
    session open. Lives on the CaseStudy itself so each commit produces a
    new CaseStudy revision (full audit trail of the workspace evolution).
    """

    title: Annotated[str, DisplayName()]
    description: str
    owner: str = "unknown"
    status: CaseStatus = "active"
    defect_type: str | None = None
    process_module: str | None = None
    scan_stage: str | None = None
    tags: list[str] = []
    workspace_archive: Binary | None = None
    last_stale_notify_at: str | None = None
