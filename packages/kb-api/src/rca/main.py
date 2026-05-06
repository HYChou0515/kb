"""kb-api — thin HTTP wrapper over cognee v1.

Five routes + /health. No typed records, no custom pipelines, no
extraction/reasoning services. Everything goes through cognee directly:

    POST   /remember   → cognee.remember
    POST   /recall     → cognee.recall
    POST   /search     → cognee.search
    POST   /improve    → cognee.improve   (cognee v1's "new cognify")
    DELETE /forget     → cognee.forget
    GET    /health     → liveness probe

Trust tier signal lives on `dataset_name` (e.g., "rca_reports" /
"rca_literature" / "rca_conversations") rather than typed records.

Run:
    uv run uvicorn rca.main:app --host 127.0.0.1 --port 8765 --reload
    # or:
    uv run kb-api
"""

from __future__ import annotations

# IMPORTANT: import rca.config BEFORE cognee — config's module-level
# _eager_export_cognee_paths() must run first, otherwise cognee's logger
# initializes against its default site-packages path and prints a
# misleading "Database storage: <venv>/.../cognee/..." line.
from rca.config import load_settings  # noqa: I001 — order matters

import logging
import traceback
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import cognee
from cognee.modules.search.types import SearchType
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─── request / response models ───────────────────────────────────────────


class RememberRequest(BaseModel):
    text: str | list[str]
    dataset_name: str = "main_dataset"
    session_id: str | None = None
    self_improvement: bool = True
    run_in_background: bool = False
    label: str | None = None  # optional caller-side hint (logged, not stored)


class RecallRequest(BaseModel):
    query: str = Field(..., min_length=1)
    datasets: list[str] | None = None
    top_k: int = 10
    session_id: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    query_type: str = "GRAPH_COMPLETION"
    datasets: list[str] | None = None
    top_k: int = 10


class ImproveRequest(BaseModel):
    dataset: str = "main_dataset"
    run_in_background: bool = False
    session_ids: list[str] | None = None


# ─── app ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings.export_to_cognee_env()
    logger.info("kb-api ready (cognee thin proxy)")
    yield


app = FastAPI(
    title="RCA Knowledge Base API",
    version="1.0.0",
    description=(
        "Thin HTTP wrapper over cognee v1. Routes map 1:1 to cognee primitives "
        "(remember / recall / search / improve / forget). Trust tier signal "
        "is encoded as dataset_name."
    ),
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/remember")
async def remember(req: RememberRequest) -> dict[str, Any]:
    if req.label:
        logger.info("remember: dataset=%s label=%s", req.dataset_name, req.label)
    result = await cognee.remember(
        req.text,
        dataset_name=req.dataset_name,
        session_id=req.session_id,
        self_improvement=req.self_improvement,
        run_in_background=req.run_in_background,
    )
    return _serialize(result)


@app.post("/recall")
async def recall(req: RecallRequest) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if req.session_id is not None:
        # cognee.recall takes session_id via **kwargs (RecallKwargs).
        kwargs["session_id"] = req.session_id
    results = await cognee.recall(
        req.query,
        datasets=req.datasets,
        top_k=req.top_k,
        **kwargs,
    )
    return {"results": _serialize(results)}


@app.post("/search")
async def search(req: SearchRequest) -> dict[str, Any]:
    try:
        st = SearchType[req.query_type]
    except KeyError as exc:
        valid = sorted(t.name for t in SearchType)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown query_type {req.query_type!r}. Valid: {valid}",
        ) from exc
    results = await cognee.search(
        req.query,
        query_type=st,
        datasets=req.datasets,
        top_k=req.top_k,
    )
    return {"results": _serialize(results)}


@app.post("/improve")
async def improve(req: ImproveRequest) -> dict[str, Any]:
    result = await cognee.improve(
        dataset=req.dataset,
        run_in_background=req.run_in_background,
        session_ids=req.session_ids,
    )
    return _serialize(result) if result else {"status": "queued"}


@app.delete("/forget")
async def forget(
    data_id: str | None = Query(None),
    dataset: str | None = Query(None),
    everything: bool = Query(False),
) -> dict[str, Any]:
    """Delete data from cognee. Pass exactly one of (data_id, dataset)
    or set everything=true."""
    if not (data_id or dataset or everything):
        raise HTTPException(
            status_code=400,
            detail="Pass one of: data_id=<uuid> | dataset=<name|uuid> | everything=true",
        )
    parsed_data_id: UUID | None = None
    if data_id:
        try:
            parsed_data_id = UUID(data_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"data_id must be a UUID: {exc}"
            ) from exc

    parsed_dataset: str | UUID | None = dataset
    if dataset:
        try:
            parsed_dataset = UUID(dataset)
        except ValueError:
            parsed_dataset = dataset

    result = await cognee.forget(
        data_id=parsed_data_id,
        dataset=parsed_dataset,
        everything=everything,
    )
    return _serialize(result) if isinstance(result, dict) else {"status": "ok"}


@app.exception_handler(Exception)
async def _verbose_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    cls = exc.__class__.__name__
    msg = str(exc)
    status = 500
    hint = ""
    if "AuthenticationError" in cls or "incorrect api key" in msg.lower():
        status = 502
        hint = (
            " | Hint: the LLM provider rejected the API key. "
            "Check OPENAI_API_KEY / ANTHROPIC_API_KEY in .env."
        )
    elif "RateLimitError" in cls:
        status = 429
        hint = " | Hint: LLM provider rate-limited."
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status,
        content={
            "detail": f"{cls}: {msg}{hint}",
            "exception_type": cls,
            "path": str(request.url.path),
        },
    )


# ─── helpers ─────────────────────────────────────────────────────────────


def _serialize(obj: Any) -> Any:
    """Best-effort JSON-friendly representation for cognee return objects.
    cognee returns Pydantic models, dataclasses, or plain dicts depending
    on the call — normalize all of them."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def run() -> None:
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        "rca.main:app",
        host=settings.kb_api_host,
        port=settings.kb_api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
