"""AutoCrudWrapper — owns an AutoCRUD instance, hides the global singleton.

Implements ports.out.autocrud.IAutoCrudWrapper. Construction:
    1. Build the AutoCRUD instance (with cognee mirror handler).
    2. Register all six domain models with their indexed fields.
Then at app startup (lifespan):
    3. wrapper.register_actions()
    4. wrapper.apply(app)

Session lifecycle actions (open / close / abandon) live on this class as
bound methods. AutoCRUD inspects the bound method's signature (which
hides ``self``) when generating routes, so they look like plain action
functions to the framework while keeping access to ``self.case_study_mgr``
without the closure-factory indirection that confuses Pylance.
"""

import datetime as dt
import logging
import shutil
import uuid
from pathlib import Path
from typing import Annotated, Any, cast

from autocrud import AutoCRUD, Ref
from autocrud.crud.route_templates.basic import DependencyProvider
from autocrud.message_queue import SimpleMessageQueueFactory
from autocrud.resource_manager import DiskStorageFactory, Encoding, ResourceManager
from autocrud.types import IResourceManager
from autocrud.types import Binary
from msgspec import structs

from rca.adapter.out.autocrud.actions.report import sign_report
from rca.adapter.out.autocrud.actions.session import (
    ACTIVE_SESSIONS_DIR,
    TRANSCRIPTS_DIR,
    ensure_dirs,
    is_set,
    tar_active_dir,
    untar_to_dir,
)
from rca.adapter.out.autocrud.cognee_mirror import CogneeMirrorHandler
from rca.config import Settings
from rca.domain.agent_feedback import AgentFeedback
from rca.domain.case_study import CaseStudy
from rca.domain.document import DocumentSource
from rca.domain.glossary import GlossaryEntry
from rca.domain.rca_report import RCAReport
from rca.domain.session import Session
from rca.ports.out.autocrud import IAutoCrudWrapper

logger = logging.getLogger(__name__)


class AutoCrudWrapper(IAutoCrudWrapper):
    def __init__(self, settings: Settings, mirror: CogneeMirrorHandler) -> None:
        settings.autocrud_data_root.mkdir(parents=True, exist_ok=True)

        self.crud = AutoCRUD(
            storage_factory=DiskStorageFactory(str(settings.autocrud_data_root)),
            message_queue_factory=SimpleMessageQueueFactory(),
            dependency_provider=DependencyProvider(
                get_user=lambda: settings.autocrud_user,
                get_now=lambda: dt.datetime.now(dt.UTC),
            ),
            model_naming="kebab",
            encoding=Encoding.json,
            event_handlers=[mirror],
        )
        self._register_models()
        logger.info(
            "AutoCrudWrapper initialized (data_root=%s)", settings.autocrud_data_root
        )

    def _register_models(self) -> None:
        self.crud.add_model(
            CaseStudy,
            indexed_fields=[
                ("status", str),
                ("owner", str),
                ("defect_type", str),
                ("process_module", str),
            ],
        )
        self.crud.add_model(
            Session,
            indexed_fields=[
                ("status", str),
                ("case_study_id", str),
                ("rca_completed", bool),
            ],
        )
        self.crud.add_model(
            RCAReport,
            indexed_fields=[
                ("case_study_id", str),
                ("session_id", str),
                ("agreed", bool),
                ("verification_status", str),
            ],
        )
        self.crud.add_model(
            GlossaryEntry,
            indexed_fields=[
                ("term", str),
                ("source_session_id", str),
                ("source_case_study_id", str),
                ("confidence", str),
            ],
        )
        self.crud.add_model(
            AgentFeedback,
            indexed_fields=[
                ("type", str),
                ("topic", str),
                ("source_session_id", str),
                ("source_case_study_id", str),
            ],
        )
        self.crud.add_model(
            DocumentSource,
            indexed_fields=[
                ("source_kind", str),
                ("case_study_id", str),
                ("session_id", str),
            ],
        )

    # ─── typed resource manager accessors ──────────────────────────────────

    def case_study_mgr(self) -> IResourceManager[CaseStudy]:
        return self.crud.get_resource_manager(CaseStudy)

    def session_mgr(self) -> IResourceManager[Session]:
        return self.crud.get_resource_manager(Session)

    def rca_report_mgr(self) -> IResourceManager[RCAReport]:
        return self.crud.get_resource_manager(RCAReport)

    def glossary_mgr(self) -> IResourceManager[GlossaryEntry]:
        return self.crud.get_resource_manager(GlossaryEntry)

    def agent_feedback_mgr(self) -> IResourceManager[AgentFeedback]:
        return self.crud.get_resource_manager(AgentFeedback)

    def document_mgr(self) -> IResourceManager[DocumentSource]:
        return self.crud.get_resource_manager(DocumentSource)

    # ─── session lifecycle (bound to self via case_study_mgr) ─────────────

    def _load_case_workspace_bytes(self, case_id: str) -> bytes | None:
        rm = self.case_study_mgr()
        resource = rm.get(case_id)
        if resource is None:
            raise ValueError(f"CaseStudy {case_id} not found")
        case = resource.data
        arch = case.workspace_archive
        if arch is None:
            return None
        file_id = getattr(arch, "file_id", None)
        if not is_set(file_id):
            return None
        blob = rm.get_blob(file_id)
        data = getattr(blob, "data", None)
        if not isinstance(data, (bytes, bytearray)):
            logger.warning("workspace blob for case %s has no data", case_id)
            return None
        return bytes(data)

    def _commit_workspace_to_case(
        self, case_id: str, tar_bytes: bytes, session_token: str
    ) -> None:
        # `user_ctx` / `now_ctx` are concrete-impl attributes that
        # IResourceManager does not expose, so we cast to the concrete
        # ResourceManager here. This is safe — the AutoCRUD instance
        # always returns ResourceManager from get_resource_manager().
        rm = cast(ResourceManager[CaseStudy], self.crud.get_resource_manager(CaseStudy))
        resource = rm.get(case_id)
        if resource is None:
            raise ValueError(f"CaseStudy {case_id} not found")
        case = resource.data
        new_archive = Binary(data=tar_bytes, content_type="application/gzip")
        new_case = structs.replace(case, workspace_archive=new_archive)
        # AutoCRUD per-request ContextVars (now_ctx/user_ctx) are scoped to
        # the CURRENT resource's manager. Cross-resource updates need them
        # set explicitly via autocrud's Ctx.ctx() helper. (Ctx[T] generic
        # inference confuses ty — the literal values are correct at runtime.)
        with (
            rm.user_ctx.ctx("system"),
            rm.now_ctx.ctx(dt.datetime.now(dt.UTC)),
        ):
            rm.update(case_id, new_case)
        logger.info(
            "CaseStudy %s workspace_archive updated (%d bytes, session=%s)",
            case_id,
            len(tar_bytes),
            session_token,
        )

    async def open_session(self, case_id: Annotated[str, Ref("case-study")]) -> Session:
        ensure_dirs()

        sess_token = uuid.uuid4().hex[:8]
        active_dir = ACTIVE_SESSIONS_DIR / case_id / sess_token
        active_dir.mkdir(parents=True, exist_ok=True)

        n_loaded = 0
        tar_bytes = self._load_case_workspace_bytes(case_id)
        if tar_bytes is not None:
            n_loaded = untar_to_dir(tar_bytes, active_dir)
            logger.info(
                "session opened: case=%s active_dir=%s (hydrated %d files)",
                case_id,
                active_dir,
                n_loaded,
            )
        else:
            logger.info(
                "session opened: case=%s active_dir=%s (fresh — no prior workspace)",
                case_id,
                active_dir,
            )

        return Session(
            case_study_id=case_id,
            status="active",
            opened_at=dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            workspace_path=str(active_dir),
            rca_completed=False,
            notes=f"hydrated {n_loaded} files from CaseStudy.workspace_archive"
            if n_loaded
            else "fresh session (no prior commits)",
        )

    async def close_session(self, existing: Session) -> Session:
        ensure_dirs()

        if existing.status != "active":
            raise ValueError(f"Cannot close session in status={existing.status!r}")
        if not existing.workspace_path:
            raise ValueError("Session has no workspace_path")

        active_dir = Path(existing.workspace_path)
        if not active_dir.exists():
            raise ValueError(f"Active dir not found: {active_dir}")

        case_id = existing.case_study_id
        sess_token = active_dir.name

        transcript_in_active = active_dir / "transcript.json"
        transcript_path: str | None = None
        if transcript_in_active.exists():
            case_transcripts = TRANSCRIPTS_DIR / case_id
            case_transcripts.mkdir(parents=True, exist_ok=True)
            out = case_transcripts / f"{sess_token}.json"
            shutil.copy2(transcript_in_active, out)
            transcript_path = str(out)
            logger.info("transcript archived: %s → %s", transcript_in_active, out)

        tar_bytes = tar_active_dir(active_dir)
        self._commit_workspace_to_case(case_id, tar_bytes, sess_token)

        shutil.rmtree(active_dir)
        logger.info("active dir removed: %s", active_dir)

        existing.status = "closed"
        existing.closed_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        if transcript_path:
            existing.transcript_path = transcript_path
        return existing

    async def abandon_session(self, existing: Session) -> Session:
        ensure_dirs()

        if existing.status != "active":
            raise ValueError(f"Cannot abandon session in status={existing.status!r}")

        active_dir = Path(existing.workspace_path) if existing.workspace_path else None
        if active_dir and active_dir.exists():
            shutil.rmtree(active_dir)
            logger.info("session abandoned, active dir removed: %s", active_dir)

        existing.status = "abandoned"
        existing.closed_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return existing

    # ─── runtime registration of custom actions ────────────────────────────

    def register_actions(self) -> None:
        # Bound methods — AutoCRUD's signature inspection automatically hides
        # `self`, so these look like plain action functions to the framework.
        self.crud.create_action(
            "session", path="/open/{case_id}", label="Open Session"
        )(self.open_session)
        self.crud.update_action("session", label="Close Session")(self.close_session)
        self.crud.update_action("session", label="Abandon Session")(
            self.abandon_session
        )

        self.crud.update_action("rca-report", path="/sign", label="Sign RCA Report")(
            sign_report
        )
        logger.info("AutoCrudWrapper: actions registered")

    def apply(self, app: Any) -> None:
        self.crud.apply(app)
