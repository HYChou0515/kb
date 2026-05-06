"""Workspace HTTP routes — open / close / finalize.

POST /case-study/{case_id}/open-workspace
    First-time or resume: creates/restores workspace, spawns opencode session.
    Returns session_id, opencode_session_id, opencode_url, workspace_path, resumed.

Additional routes (soft-close, finalize, upload-final-report) added in later phases.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from rca.container import container
from rca.domain.session import InactivityCloseReason
from rca.ports.out.autocrud import IAutoCrudWrapper
from rca.services.digest import digest_session
from rca.services.workspace_lifecycle import (
    AnotherCaseActiveError,
    finalize_workspace,
    open_workspace,
    soft_close_workspace,
    upload_final_report,
)


async def _safe_digest(session_id: str, autocrud: IAutoCrudWrapper) -> None:
    """Wrap digest so a failure never escapes the BackgroundTasks runner.

    Why: BackgroundTasks runs after the response is sent — there's no client
    to surface an error to. Log and swallow so a transient digest failure
    doesn't crash the server's task group.
    """
    try:
        await digest_session(session_id, autocrud=autocrud)
    except Exception:
        logger.warning(
            "background digest failed for session %s (ignored)",
            session_id,
            exc_info=True,
        )


logger = logging.getLogger(__name__)

router = APIRouter(tags=["workspace"])


@router.post("/case-study/{case_id}/open-workspace")
async def open_workspace_endpoint(case_id: str) -> JSONResponse:
    """Open (or resume) the workspace for a CaseStudy.

    Creates a workspace directory, seeds template files, spawns an opencode
    session, and returns the session URL so the user can open the chat.

    400 — CaseStudy is in "closed" status (PATCH to "active" first).
    404 — case_id does not exist.
    409 — a different CaseStudy already has an active session (the local
          opencode runtime is single-cwd; soft-close that session first).
    """
    try:
        result = await open_workspace(
            case_id,
            autocrud=container.autocrud(),
            opencode=container.opencode(),
        )
    except AnotherCaseActiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        cls = exc.__class__.__name__
        if "NotFound" in cls or "not found" in str(exc).lower():
            raise HTTPException(
                status_code=404, detail=f"CaseStudy {case_id!r} not found"
            ) from exc
        raise

    return JSONResponse(
        {
            "session_id": result.session_id,
            "opencode_session_id": result.opencode_session_id,
            "opencode_url": result.opencode_url,
            "workspace_path": result.workspace_path,
            "resumed": result.resumed,
        }
    )


@router.post("/session/{session_id}/soft-close")
async def soft_close_endpoint(
    session_id: str,
    background_tasks: BackgroundTasks,
    reason: InactivityCloseReason = "explicit_close",
) -> JSONResponse:
    """Soft-close an active session.

    Tars the workspace, commits to CaseStudy.workspace_archive, removes the
    active workspace directory, and updates the Session to status='closed'.
    The opencode session is preserved in opencode's SQLite for cheap resume.

    Digest (transcript → cognee) runs as a background task after the response
    is returned — it can take seconds to minutes depending on transcript size,
    and we don't want to hold the HTTP socket open for that.

    400 — session is not in 'active' status.
    404 — session_id does not exist.
    """
    autocrud = container.autocrud()
    try:
        await soft_close_workspace(
            session_id,
            autocrud=autocrud,
            reason=reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        cls = exc.__class__.__name__
        if "NotFound" in cls or "not found" in str(exc).lower():
            raise HTTPException(
                status_code=404, detail=f"Session {session_id!r} not found"
            ) from exc
        raise
    background_tasks.add_task(_safe_digest, session_id, autocrud)
    return JSONResponse({"status": "closed", "session_id": session_id})


@router.post("/session/{session_id}/finalize")
async def finalize_endpoint(
    session_id: str,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Finalize (hard-close) an active session.

    Same as soft-close but also deletes the opencode session permanently,
    removing the chat history from opencode's SQLite. Use when the user
    explicitly marks the RCA as done.

    Digest runs as a background task after the response — see soft_close_endpoint.

    400 — session is not in 'active' status.
    404 — session_id does not exist.
    """
    autocrud = container.autocrud()
    try:
        await finalize_workspace(
            session_id,
            autocrud=autocrud,
            opencode=container.opencode(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        cls = exc.__class__.__name__
        if "NotFound" in cls or "not found" in str(exc).lower():
            raise HTTPException(
                status_code=404, detail=f"Session {session_id!r} not found"
            ) from exc
        raise
    background_tasks.add_task(_safe_digest, session_id, autocrud)
    return JSONResponse({"status": "finalized", "session_id": session_id})


@router.post("/case-study/{case_id}/upload-final-report")
async def upload_final_report_endpoint(case_id: str, file: UploadFile) -> JSONResponse:
    """Upload a final report (.md) for a CaseStudy.

    Writes the report to the active workspace as `uploaded_final_report.md`.
    If no workspace is active, auto-opens one. Returns the opencode_url so
    the user can review and submit via the chat.

    400 — non-.md file / CaseStudy is closed.
    404 — case_id does not exist.
    """
    if file.filename and not file.filename.lower().endswith(".md"):
        raise HTTPException(status_code=400, detail="Only .md files are accepted")

    content = await file.read()
    try:
        result = await upload_final_report(
            case_id,
            report_content=content.decode("utf-8", errors="replace"),
            autocrud=container.autocrud(),
            opencode=container.opencode(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        cls = exc.__class__.__name__
        if "NotFound" in cls or "not found" in str(exc).lower():
            raise HTTPException(
                status_code=404, detail=f"CaseStudy {case_id!r} not found"
            ) from exc
        raise
    return JSONResponse(
        {
            "session_id": result.session_id,
            "opencode_url": result.opencode_url,
            "message": (
                "Final report uploaded. Open the workspace to review and submit."
            ),
        }
    )
