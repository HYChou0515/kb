"""/admin/* + /health APIRouter."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from rca.container import get_kb
from rca.ports.in_.admin import CognifyRequest, StatusResponse
from rca.services.kb import IKBService

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
