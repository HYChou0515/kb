"""Workspace HTTP routes — open / close / finalize.

POST /case-study/{case_id}/open-workspace
    First-time or resume: creates/restores workspace, spawns opencode session.
    Returns session_id, opencode_session_id, opencode_url, workspace_path, resumed.

Additional routes (soft-close, finalize, upload-final-report) added in later phases.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from rca.container import container
from rca.services.workspace_lifecycle import open_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workspace"])


@router.post("/case-study/{case_id}/open-workspace")
async def open_workspace_endpoint(case_id: str) -> JSONResponse:
    """Open (or resume) the workspace for a CaseStudy.

    Creates a workspace directory, seeds template files, spawns an opencode
    session, and returns the session URL so the user can open the chat.

    400 — CaseStudy is in "closed" status (PATCH to "active" first).
    404 — case_id does not exist.
    """
    try:
        result = await open_workspace(
            case_id,
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
            "opencode_session_id": result.opencode_session_id,
            "opencode_url": result.opencode_url,
            "workspace_path": result.workspace_path,
            "resumed": result.resumed,
        }
    )
