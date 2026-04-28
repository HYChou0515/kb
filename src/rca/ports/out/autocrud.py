"""AutoCRUD outbound port — typed access to the AutoCRUD instance.

Wraps `autocrud.AutoCRUD(...)` so domain code never imports the
library's global `crud` singleton. Implementation:
adapter.out.autocrud.wrapper.AutoCrudWrapper.
"""

from __future__ import annotations

from typing import Any, Protocol


class IAutoCrudWrapper(Protocol):
    """Typed accessors for the underlying AutoCRUD instance.

    Each `*_mgr()` returns a ResourceManager bound to the corresponding
    domain type. Using `Any` for the return type is intentional: the
    autocrud library's ResourceManager generic is not part of this
    project's coupling surface — the methods we actually use
    (`.get(id)`, `.get_blob(file_id)`, `.update(id, new_record)`) are
    stable across autocrud versions.
    """

    def session_mgr(self) -> Any: ...
    def case_study_mgr(self) -> Any: ...
    def rca_report_mgr(self) -> Any: ...
    def glossary_mgr(self) -> Any: ...
    def agent_feedback_mgr(self) -> Any: ...
    def document_mgr(self) -> Any: ...

    def register_actions(self) -> None: ...
    def apply(self, app: Any) -> None: ...
