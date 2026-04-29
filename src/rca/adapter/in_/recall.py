"""/recall APIRouter — thin wrapper around KBService.recall."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from rca.container import get_kb
from rca.ports.in_.recall import (
    RecallAssessmentResponse,
    RecallRequest,
    RecallSnippetsResponse,
    RecallSynthesisResponse,
)
from rca.services.kb import IKBService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recall"])


@router.post("/recall")
async def recall(
    req: RecallRequest,
    kb: Annotated[IKBService, Depends(get_kb)],
) -> RecallSnippetsResponse | RecallAssessmentResponse | RecallSynthesisResponse:
    return await kb.recall(req)
