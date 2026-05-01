"""AutoCRUD outbound port — typed access to the AutoCRUD instance.

Wraps `autocrud.AutoCRUD(...)` so domain code never imports the
library's global `crud` singleton. Implementation:
adapter.out.autocrud.wrapper.AutoCrudWrapper.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from autocrud.resource_manager import ResourceManager
from typing import Any

from rca.domain.document import DocumentSource
from rca.domain.agent_feedback import AgentFeedback
from rca.domain.glossary import GlossaryEntry
from rca.domain.case_study import CaseStudy
from rca.domain.rca_report import RCAReport
from rca.domain.session import Session


class IAutoCrudWrapper(ABC):
    """Typed accessors for the underlying AutoCRUD instance.

    Each `*_mgr()` returns a ResourceManager bound to the corresponding
    domain type. Using `Any` for the return type is intentional: the
    autocrud library's ResourceManager generic is not part of this
    project's coupling surface — the methods we actually use
    (`.get(id)`, `.get_blob(file_id)`, `.update(id, new_record)`) are
    stable across autocrud versions.
    """

    @abstractmethod
    def session_mgr(self) -> ResourceManager[Session]: ...

    @abstractmethod
    def case_study_mgr(self) -> ResourceManager[CaseStudy]: ...

    @abstractmethod
    def rca_report_mgr(self) -> ResourceManager[RCAReport]: ...

    @abstractmethod
    def glossary_mgr(self) -> ResourceManager[GlossaryEntry]: ...

    @abstractmethod
    def agent_feedback_mgr(self) -> ResourceManager[AgentFeedback]: ...

    @abstractmethod
    def document_mgr(self) -> ResourceManager[DocumentSource]: ...

    @abstractmethod
    async def close_session(self, existing: Session) -> Session:
        """Tar the active workspace, commit to CaseStudy, remove active_dir,
        update session status to 'closed'. Called by soft-close service code."""
        ...

    @abstractmethod
    async def abandon_session(self, existing: Session) -> Session:
        """Drop the active workspace without committing, update session status
        to 'abandoned'. Called by abandon service code."""
        ...

    @abstractmethod
    def register_actions(self) -> None: ...

    @abstractmethod
    def apply(self, app: Any) -> None: ...
