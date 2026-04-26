"""KB API — FastAPI app exposing retain / recall / admin endpoints.

Run:
    uv run uvicorn kb_api.main:app --host 127.0.0.1 --port 8765 --reload

Or via the console script:
    uv run kb-api
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator, Literal

from cognee.api.v1.search import SearchType
from cognee.api.v1.visualize import visualize_graph
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from kb_api.schemas import (
    CognifyRequest,
    RecallAssessmentResponse,
    RecallRequest,
    RecallSnippetsResponse,
    RecallSynthesisResponse,
    RetainConversationRequest,
    RetainExtractionRequest,
    RetainResponse,
    RetainTextRequest,
    StatusResponse,
)
from rca_knowledge.config import load_settings
from rca_knowledge.graph.cognee_client import CogneeClient
from rca_knowledge.ingestion.extractor import (
    ExtractionResult,
    SemiconductorExtractor,
)
from rca_knowledge.ingestion.pipeline import IngestionPipeline
from rca_knowledge.reasoning.causal_query import CausalReasoner

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = load_settings()
    app.state.settings = settings
    app.state.cognee = CogneeClient(settings)
    app.state.pipeline = IngestionPipeline(settings)
    app.state.reasoner = CausalReasoner(settings, cognee_client=app.state.cognee)
    app.state.extractor = SemiconductorExtractor(settings)
    await app.state.cognee.setup()
    logger.info("KB API ready")
    yield


app = FastAPI(
    title="RCA Knowledge Base API",
    version="0.2.0",
    description="retain (write) + recall (read) for the semiconductor RCA knowledge graph.",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def _verbose_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Surface internal errors as JSON instead of FastAPI's empty 500 body.

    Recognized upstream-LLM auth errors are mapped to 502 with a clear hint.
    """
    cls = exc.__class__.__name__
    msg = str(exc)
    # Prefer 502 (bad gateway) for LLM provider failures so callers can
    # tell "your service is fine, the upstream LLM rejected the call".
    status = 500
    hint = ""
    if "AuthenticationError" in cls or "incorrect api key" in msg.lower():
        status = 502
        hint = (
            " | Hint: the LLM provider rejected the API key. Check OPENAI_API_KEY"
            " (or ANTHROPIC_API_KEY) in .env — common causes: extra quotes,"
            " trailing whitespace, key revoked, or the key's project doesn't"
            " allow this model."
        )
    elif "RateLimitError" in cls:
        status = 429
        hint = " | Hint: LLM provider rate-limited. Wait or reduce concurrency."
    logger.error("Unhandled exception on %s %s: %s\n%s", request.method, request.url.path, exc, traceback.format_exc())
    return JSONResponse(
        status_code=status,
        content={
            "detail": f"{cls}: {msg}{hint}",
            "exception_type": cls,
            "path": str(request.url.path),
        },
    )


@app.get("/health", response_model=StatusResponse)
async def health() -> StatusResponse:
    return StatusResponse(ok=True, detail="kb-api alive")


# ---- retain ----------------------------------------------------------------

def _node_set_for(source_kind: Literal["literature", "conversation"]) -> list[str]:
    return ["rca_literature"] if source_kind == "literature" else ["rca_conversations"]


def _summarize_results(results) -> RetainResponse:
    n_e = sum(len(r.extraction.entities) for r in results)
    n_r = sum(len(r.extraction.relations) for r in results)
    summaries = [r.extraction.summary for r in results if r.extraction.summary]
    return RetainResponse(
        chunks_ingested=len(results),
        entities_extracted=n_e,
        relations_extracted=n_r,
        summary=" | ".join(summaries[:3]),
        source_labels=[r.source_label for r in results],
    )


@app.post("/retain/text", response_model=RetainResponse)
async def retain_text(req: RetainTextRequest) -> RetainResponse:
    pipeline: IngestionPipeline = app.state.pipeline
    results = await pipeline.ingest_text(
        req.text,
        source_label=req.label,
        dataset=req.dataset,
        node_set=_node_set_for(req.source_kind),
        run_cognify=req.cognify,
    )
    return _summarize_results(results)


@app.post("/retain/file", response_model=RetainResponse)
async def retain_file(
    file: Annotated[UploadFile, File()],
    label: Annotated[str | None, Form()] = None,
    dataset: Annotated[str, Form()] = "rca",
    cognify: Annotated[bool, Form()] = True,
    source_kind: Annotated[str, Form()] = "literature",
) -> RetainResponse:
    if file.filename is None:
        raise HTTPException(400, "file has no name")
    suffix = Path(file.filename).suffix
    pipeline: IngestionPipeline = app.state.pipeline
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    try:
        results = await pipeline.ingest_file(
            tmp_path,
            dataset=dataset,
            node_set=_node_set_for(source_kind),  # type: ignore[arg-type]
            run_cognify=cognify,
        )
    finally:
        tmp_path.unlink(missing_ok=True)
    resp = _summarize_results(results)
    if label:
        resp.source_labels = [f"{label}:{s}" for s in resp.source_labels]
    return resp


@app.post("/retain/conversation", response_model=RetainResponse)
async def retain_conversation(req: RetainConversationRequest) -> RetainResponse:
    pipeline: IngestionPipeline = app.state.pipeline
    results = await pipeline.ingest_conversation(
        req.messages,
        session_id=req.session_id,
        dataset=req.dataset,
        run_cognify=req.cognify,
    )
    return _summarize_results(results)


@app.post("/retain/extraction", response_model=RetainResponse)
async def retain_extraction(req: RetainExtractionRequest) -> RetainResponse:
    """Push a pre-extracted ExtractionResult straight into the graph,
    skipping internal LLM extraction. Useful when an external system
    (Claude/GPT/etc.) already did the extraction and you just want to
    deposit the structured knowledge.
    """
    cognee = app.state.cognee
    rendered = SemiconductorExtractor.render_for_cognee(
        req.extraction, source_label=req.source_label
    )
    await cognee.add_text(
        rendered, dataset=req.dataset, node_set=_node_set_for(req.source_kind)
    )
    if req.cognify:
        await cognee.cognify(dataset=req.dataset)

    return RetainResponse(
        chunks_ingested=1,
        entities_extracted=len(req.extraction.entities),
        relations_extracted=len(req.extraction.relations),
        summary=req.extraction.summary,
        source_labels=[req.source_label],
    )


# ---- recall ----------------------------------------------------------------

@app.post("/recall")
async def recall(req: RecallRequest):
    if req.mode == "snippets":
        snippets = await app.state.reasoner.retrieve_context(
            req.query, req.process_context, top_k=req.top_k
        )
        snippets = _filter_by_source(snippets, req.source_filter)
        return RecallSnippetsResponse(snippets=snippets[: req.top_k])

    if req.mode == "assessment":
        # The assessor pulls its own context internally. We pass the query as
        # a "correlation" string and the optional process context.
        assessment = await app.state.reasoner.assess(
            req.query,
            process_context=req.process_context,
            top_k=req.top_k,
        )
        return RecallAssessmentResponse(assessment=assessment)

    if req.mode == "synthesis":
        results = await app.state.cognee.search(
            req.query,
            search_type=SearchType.GRAPH_COMPLETION,
            top_k=req.top_k,
        )
        text_results: list[str] = [str(r) for r in results]
        synthesis = "\n\n".join(text_results) if text_results else "(no graph match)"
        return RecallSynthesisResponse(synthesis=synthesis, raw=text_results)

    raise HTTPException(400, f"unknown mode: {req.mode}")


def _filter_by_source(snippets: list[str], source_filter: str) -> list[str]:
    """Best-effort filter by node_set marker baked into the rendered text.

    POC heuristic — conversation chunks carry the literal `rca_conversations`
    string in their rendered provenance; everything else is literature.
    """
    if source_filter == "all":
        return snippets
    if source_filter == "conversations":
        return [s for s in snippets if "rca_conversations" in s]
    return [s for s in snippets if "rca_conversations" not in s]


# ---- admin -----------------------------------------------------------------

@app.post("/admin/cognify", response_model=StatusResponse)
async def admin_cognify(req: CognifyRequest) -> StatusResponse:
    await app.state.cognee.cognify(dataset=req.dataset)
    return StatusResponse(ok=True, detail=f"cognify(dataset={req.dataset}) done")


@app.delete("/admin/prune", response_model=StatusResponse)
async def admin_prune() -> StatusResponse:
    await app.state.cognee.prune()
    return StatusResponse(ok=True, detail="cognee stores pruned")


@app.get("/admin/graph", response_class=HTMLResponse)
async def admin_graph() -> HTMLResponse:
    """Render the entire knowledge graph as an interactive HTML page.

    Backed by cognee's built-in ``visualize_graph`` — returns a standalone
    self-contained HTML document with vis-network embedded. Just open
    http://<host>:<port>/admin/graph in a browser.
    """
    await app.state.cognee.setup()
    html = await visualize_graph()
    return HTMLResponse(content=html)


# ---- runner ----------------------------------------------------------------

def run() -> None:  # console-script entry
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        "kb_api.main:app",
        host=settings.kb_api_host,
        port=settings.kb_api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
