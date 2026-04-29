"""/retain/* APIRouter — thin wrappers around KBService.retain_*."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from rca.ports.in_.retain import (
    RetainConversationRequest,
    RetainExtractionRequest,
    RetainResponse,
    RetainTextRequest,
)
from rca.services.kb import IKBService, SourceKind

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retain", tags=["retain"])


def get_kb(request: Request) -> IKBService:
    return request.app.state.kb


@router.post("/text", response_model=RetainResponse)
async def retain_text(
    req: RetainTextRequest,
    kb: Annotated[IKBService, Depends(get_kb)],
) -> RetainResponse:
    return await kb.retain_text(req)


@router.post("/file", response_model=RetainResponse)
async def retain_file(
    file: Annotated[UploadFile, File()],
    kb: Annotated[IKBService, Depends(get_kb)],
    label: Annotated[str | None, Form()] = None,
    dataset: Annotated[str, Form()] = "rca",
    cognify: Annotated[bool, Form()] = True,
    source_kind: Annotated[
        Literal["literature", "conversation", "rca_report"], Form()
    ] = "literature",
) -> RetainResponse:
    if file.filename is None:
        raise HTTPException(400, "file has no name")
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    sk: SourceKind = source_kind
    try:
        return await kb.retain_file(
            tmp_path,
            label=label,
            dataset=dataset,
            cognify=cognify,
            source_kind=sk,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/conversation", response_model=RetainResponse)
async def retain_conversation(
    req: RetainConversationRequest,
    kb: Annotated[IKBService, Depends(get_kb)],
) -> RetainResponse:
    return await kb.retain_conversation(req)


@router.post("/extraction", response_model=RetainResponse)
async def retain_extraction(
    req: RetainExtractionRequest,
    kb: Annotated[IKBService, Depends(get_kb)],
) -> RetainResponse:
    return await kb.retain_extraction(req)
