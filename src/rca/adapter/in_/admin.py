"""/admin/* + /health APIRouter."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from rca.container import container, get_kb
from rca.ports.in_.admin import CognifyRequest, StatusResponse
from rca.services.kb import IKBService
from rca.services.stale_notify import find_stale_cases, notify_stale_cases

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


@router.get("/health", response_model=StatusResponse)
async def health() -> StatusResponse:
    return StatusResponse(ok=True, detail="kb-api alive")


@router.post("/admin/cognify", response_model=StatusResponse)
async def admin_cognify(
    req: CognifyRequest,
    kb: Annotated[IKBService, Depends(get_kb)],
) -> StatusResponse:
    return await kb.admin_cognify(req)


@router.delete("/admin/prune", response_model=StatusResponse)
async def admin_prune(
    kb: Annotated[IKBService, Depends(get_kb)],
) -> StatusResponse:
    return await kb.admin_prune()


@router.get("/admin/graph", response_class=HTMLResponse)
async def admin_graph(
    kb: Annotated[IKBService, Depends(get_kb)],
) -> HTMLResponse:
    """Render the entire knowledge graph as an interactive HTML page.
    The HTML rendering is owned by IKBService.visualize_graph() so cognee
    coupling stays inside the service layer.
    """
    return HTMLResponse(content=await kb.visualize_graph())


@router.get("/admin/stale-cases")
async def admin_stale_cases() -> JSONResponse:
    """List active CaseStudy records older than 7 days with no agreed RCAReport."""
    stale = find_stale_cases(container.autocrud())
    return JSONResponse(
        [
            {
                "case_id": s.case_id,
                "title": s.title,
                "created_time": s.created_time.isoformat(),
                "last_stale_notify_at": s.last_stale_notify_at,
            }
            for s in stale
        ]
    )


@router.post("/admin/notify-stale-cases")
async def admin_notify_stale_cases() -> JSONResponse:
    """Log warnings for stale cases and update their last_stale_notify_at."""
    count = notify_stale_cases(container.autocrud())
    logger.info("stale case notification sweep: %d case(s) notified", count)
    return JSONResponse({"notified": count})
