"""/admin/* + /health APIRouter."""

from __future__ import annotations

import logging
from typing import Annotated

from cognee.api.v1.visualize import visualize_graph
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from rca.ports.in_.admin import CognifyRequest, StatusResponse
from rca.services.kb import IKBService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


def get_kb(request: Request) -> IKBService:
    return request.app.state.kb


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

    Calls cognee's visualize_graph directly — kept as a thin admin endpoint
    rather than a KBService method since the only caller is this debug
    page and the return type is HTML, not a structured DTO.
    """
    await kb.graph.setup()
    html = await visualize_graph()
    return HTMLResponse(content=html)
