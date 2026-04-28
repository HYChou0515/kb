"""AutoCrudWrapper — owns an AutoCRUD instance, hides the global singleton.

Implements ports.out.autocrud.IAutoCrudWrapper. Construction:
    1. Build the AutoCRUD instance (with cognee mirror handler).
    2. Register all six domain models with their indexed fields.
Then at app startup (lifespan):
    3. wrapper.register_actions()
    4. wrapper.apply(app)
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from autocrud import AutoCRUD
from autocrud.crud.route_templates.basic import DependencyProvider
from autocrud.message_queue.simple import SimpleMessageQueueFactory
from autocrud.resource_manager.storage_factory import DiskStorageFactory

from rca.adapter.out.autocrud.actions.report import sign_report
from rca.adapter.out.autocrud.actions.session import make_session_actions
from rca.adapter.out.autocrud.cognee_mirror import CogneeMirrorHandler
from rca.config import Settings
from rca.domain.agent_feedback import AgentFeedback
from rca.domain.case_study import CaseStudy
from rca.domain.document import DocumentSource
from rca.domain.glossary import GlossaryEntry
from rca.domain.rca_report import RCAReport
from rca.domain.session import Session

logger = logging.getLogger(__name__)


class AutoCrudWrapper:
    def __init__(self, settings: Settings, mirror: CogneeMirrorHandler) -> None:
        settings.autocrud_data_root.mkdir(parents=True, exist_ok=True)

        self.crud = AutoCRUD(
            storage_factory=DiskStorageFactory(str(settings.autocrud_data_root)),
            message_queue_factory=SimpleMessageQueueFactory(),
            dependency_provider=DependencyProvider(
                get_user=lambda: settings.autocrud_user,
                get_now=lambda: dt.datetime.utcnow(),
            ),
            model_naming="kebab",
            encoding="json",
            event_handlers=[mirror],
        )
        self._register_models()
        logger.info("AutoCrudWrapper initialized (data_root=%s)", settings.autocrud_data_root)

    def _register_models(self) -> None:
        self.crud.add_model(CaseStudy, indexed_fields=[
            ("status", str), ("owner", str), ("defect_type", str),
            ("process_module", str),
        ])
        self.crud.add_model(Session, indexed_fields=[
            ("status", str), ("case_study_id", str), ("rca_completed", bool),
        ])
        self.crud.add_model(RCAReport, indexed_fields=[
            ("case_study_id", str), ("session_id", str),
            ("agreed", bool), ("verification_status", str),
        ])
        self.crud.add_model(GlossaryEntry, indexed_fields=[
            ("term", str), ("source_session_id", str), ("source_case_study_id", str),
            ("confidence", str),
        ])
        self.crud.add_model(AgentFeedback, indexed_fields=[
            ("type", str), ("topic", str), ("source_session_id", str),
            ("source_case_study_id", str),
        ])
        self.crud.add_model(DocumentSource, indexed_fields=[
            ("source_kind", str), ("case_study_id", str), ("session_id", str),
        ])

    # ─── typed resource manager accessors ──────────────────────────────────

    def case_study_mgr(self) -> Any:
        return self.crud.get_resource_manager(CaseStudy)

    def session_mgr(self) -> Any:
        return self.crud.get_resource_manager(Session)

    def rca_report_mgr(self) -> Any:
        return self.crud.get_resource_manager(RCAReport)

    def glossary_mgr(self) -> Any:
        return self.crud.get_resource_manager(GlossaryEntry)

    def agent_feedback_mgr(self) -> Any:
        return self.crud.get_resource_manager(AgentFeedback)

    def document_mgr(self) -> Any:
        return self.crud.get_resource_manager(DocumentSource)

    # ─── runtime registration of custom actions ────────────────────────────

    def register_actions(self) -> None:
        open_session, close_session, abandon_session = make_session_actions(
            case_study_mgr_factory=self.case_study_mgr
        )
        self.crud.create_action("session", path="/open/{case_id}",
                                label="Open Session")(open_session)
        self.crud.update_action("session", label="Close Session")(close_session)
        self.crud.update_action("session", label="Abandon Session")(abandon_session)

        self.crud.update_action("rca-report", path="/sign",
                                label="Sign RCA Report")(sign_report)
        logger.info("AutoCrudWrapper: actions registered")

    def apply(self, app: Any) -> None:
        self.crud.apply(app)
