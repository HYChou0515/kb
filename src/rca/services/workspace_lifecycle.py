"""workspace_lifecycle — open / soft-close / finalize orchestration.

open_workspace() is the primary user-facing entry point. It handles:
  - first-time open: create dir + seed template + spawn opencode session
  - resume (Phase 7): reuse prior opencode_session_id + restore workspace_archive

Soft-close and finalize are added in later phases.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autocrud.types import (
    DataSearchCondition,
    DataSearchGroup,
    DataSearchLogicOperator,
    DataSearchOperator,
    ResourceMetaSearchQuery,
    ResourceMetaSearchSort,
    ResourceMetaSortDirection,
    ResourceMetaSortKey,
)

from rca.adapter.out.autocrud.actions.session import ACTIVE_SESSIONS_DIR, untar_to_dir
from rca.domain.session import InactivityCloseReason, Session
from rca.ports.out.autocrud import IAutoCrudWrapper
from rca.ports.out.opencode_runtime import IOpencodeRuntime
from rca.services.workspace_seed import seed_workspace

logger = logging.getLogger(__name__)


@dataclass
class OpenWorkspaceResult:
    session_id: str
    opencode_session_id: str
    opencode_url: str
    workspace_path: str
    resumed: bool


async def open_workspace(
    case_id: str,
    *,
    autocrud: IAutoCrudWrapper,
    opencode: IOpencodeRuntime,
) -> OpenWorkspaceResult:
    """Open (or resume) the workspace for a CaseStudy.

    First-time: creates active_sessions/<case_id>/, seeds template files,
    creates an opencode session, and persists a new Session record.

    Raises ValueError if the CaseStudy is in "closed" status.
    Raises KeyError / ResourceIDNotFoundError if case_id does not exist
    (propagated from AutoCRUD; the HTTP layer maps it to 404).
    """
    case_rm = autocrud.case_study_mgr()
    case_resource = case_rm.get(case_id)
    case = case_resource.data

    if case.status == "closed":
        raise ValueError(
            f"CaseStudy {case_id} is closed. PATCH status to 'active' before reopening."
        )

    active_dir: Path = ACTIVE_SESSIONS_DIR / case_id
    active_dir.mkdir(parents=True, exist_ok=True)

    # Restore workspace archive if this case has been worked on before.
    _restore_archive_if_present(case, case_rm, active_dir)

    # Seed template files + render CASE.md from the current CaseStudy record.
    seed_workspace(case, active_dir)

    # Resume: reuse prior opencode session if one exists (avoids spawning a new
    # opencode session and preserves the chat history from the prior session).
    prior = _find_latest_closed_session(case_id, autocrud)
    resumed = prior is not None and bool(prior.opencode_session_id)

    if resumed and prior is not None:
        oc_session_id = prior.opencode_session_id  # type: ignore[assignment]
        oc_url = prior.opencode_url or opencode.session_url(oc_session_id)
    else:
        oc_session_id = await opencode.create_session(directory=active_dir)
        oc_url = opencode.session_url(oc_session_id)

    # Persist a new Session record so watchdog, resume, and digest can find it.
    now = dt.datetime.now(dt.UTC)
    session_data = Session(
        case_study_id=case_id,
        status="active",
        opened_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        workspace_path=str(active_dir),
        opencode_session_id=oc_session_id,
        opencode_url=oc_url,
        last_activity_at=now.isoformat(),
    )
    session_rm = autocrud.session_mgr()
    rev_info = session_rm.create(session_data, user="system", now=now)

    logger.info(
        "workspace %s: case=%s session=%s opencode=%s dir=%s",
        "resumed" if resumed else "opened",
        case_id,
        rev_info.resource_id,
        oc_session_id,
        active_dir,
    )
    return OpenWorkspaceResult(
        session_id=rev_info.resource_id,
        opencode_session_id=oc_session_id,
        opencode_url=oc_url,
        workspace_path=str(active_dir),
        resumed=resumed,
    )


async def finalize_workspace(
    session_id: str,
    *,
    autocrud: IAutoCrudWrapper,
    opencode: IOpencodeRuntime,
) -> None:
    """Hard-close an active session: soft-close + permanently delete the opencode
    session (removes chat history from opencode's SQLite).

    Use soft_close_workspace() if the user may return (chat history preserved).
    Use finalize_workspace() when the user is done and wants to commit permanently.

    Raises ValueError if the session is not active.
    """
    session_rm = autocrud.session_mgr()
    session_resource = session_rm.get(session_id)
    sess = session_resource.data

    if sess.status != "active":
        raise ValueError(f"Session {session_id} is not active (status={sess.status!r})")

    oc_session_id = sess.opencode_session_id

    sess.inactivity_close_reason = "finalize"

    updated_sess = await autocrud.close_session(sess)

    now = dt.datetime.now(dt.UTC)
    session_rm.update(session_id, updated_sess, user="system", now=now)

    # Delete the opencode session — this is the point of no return.
    if oc_session_id:
        try:
            await opencode.delete_session(oc_session_id)
            logger.info(
                "opencode session deleted: session=%s opencode=%s",
                session_id,
                oc_session_id,
            )
        except Exception:
            logger.warning(
                "could not delete opencode session %s (ignored — local state already committed)",
                oc_session_id,
                exc_info=True,
            )

    logger.info("session finalized: session=%s", session_id)


async def soft_close_workspace(
    session_id: str,
    *,
    autocrud: IAutoCrudWrapper,
    reason: InactivityCloseReason = "explicit_close",
) -> None:
    """Soft-close an active session: tar workspace → commit to CaseStudy →
    remove active_dir → update session to status='closed'.

    Raises ValueError if the session is not active.
    Raises ResourceIDNotFoundError if session_id does not exist.
    """
    session_rm = autocrud.session_mgr()
    session_resource = session_rm.get(session_id)
    sess = session_resource.data

    if sess.status != "active":
        raise ValueError(f"Session {session_id} is not active (status={sess.status!r})")

    sess.inactivity_close_reason = reason

    updated_sess = await autocrud.close_session(sess)

    now = dt.datetime.now(dt.UTC)
    session_rm.update(session_id, updated_sess, user="system", now=now)
    logger.info("session soft-closed: session=%s reason=%s", session_id, reason)


# ─── helpers ─────────────────────────────────────────────────────────────────


def _find_latest_closed_session(
    case_id: str, autocrud: IAutoCrudWrapper
) -> Session | None:
    """Return the most recently created closed Session for `case_id` that has
    an opencode_session_id, or None if no such session exists."""
    session_rm = autocrud.session_mgr()
    query = ResourceMetaSearchQuery(
        conditions=[
            DataSearchGroup(
                operator=DataSearchLogicOperator.and_op,
                conditions=[
                    DataSearchCondition(
                        field_path="case_study_id",
                        operator=DataSearchOperator.equals,
                        value=case_id,
                    ),
                    DataSearchCondition(
                        field_path="status",
                        operator=DataSearchOperator.equals,
                        value="closed",
                    ),
                ],
            )
        ],
        sorts=[
            ResourceMetaSearchSort(
                key=ResourceMetaSortKey.created_time,
                direction=ResourceMetaSortDirection.descending,
            )
        ],
        limit=10,
    )
    results = session_rm.list_resources(query)
    for item in results:
        data = getattr(item, "data", None)
        if data is None:
            continue
        if isinstance(data, Session) and data.opencode_session_id:
            return data
    return None


def _restore_archive_if_present(case: object, case_rm: Any, active_dir: Path) -> None:
    arch = getattr(case, "workspace_archive", None)
    if arch is None:
        return
    file_id = getattr(arch, "file_id", None)
    if not file_id:
        return
    blob = case_rm.get_blob(file_id)
    data = getattr(blob, "data", None)
    if isinstance(data, (bytes, bytearray)):
        n = untar_to_dir(bytes(data), active_dir)
        logger.info("workspace archive restored: %d files → %s", n, active_dir)
