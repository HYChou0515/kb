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

from rca.adapter.out.autocrud.actions.session import ACTIVE_SESSIONS_DIR, untar_to_dir
from rca.domain.session import Session
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

    # Create opencode session scoped to the active workspace directory.
    oc_session_id = await opencode.create_session(directory=active_dir)
    oc_url = opencode.session_url(oc_session_id)

    # Persist the Session record so watchdog, resume, and digest can find it.
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
        "workspace opened: case=%s session=%s opencode=%s dir=%s",
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
        resumed=False,
    )


# ─── helpers ─────────────────────────────────────────────────────────────────


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
