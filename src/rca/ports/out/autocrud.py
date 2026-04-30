"""AutoCRUD outbound port — typed access to the AutoCRUD instance.

Wraps `autocrud.AutoCRUD(...)` so domain code never imports the
library's global `crud` singleton. Implementation:
adapter.out.autocrud.wrapper.AutoCrudWrapper.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

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
    def session_mgr(self) -> Any: ...

    @abstractmethod
    def case_study_mgr(self) -> Any: ...

    @abstractmethod
    def rca_report_mgr(self) -> Any: ...

    @abstractmethod
    def glossary_mgr(self) -> Any: ...

    @abstractmethod
    def agent_feedback_mgr(self) -> Any: ...

    @abstractmethod
    def document_mgr(self) -> Any: ...

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
