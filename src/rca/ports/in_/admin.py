"""Admin DTOs — request/response shapes for /admin/* and /health endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class CognifyRequest(BaseModel):
    dataset: str = "rca"


class StatusResponse(BaseModel):
    ok: bool = True
    detail: str = ""
