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

from autocrud import crud
from autocrud.crud.route_templates.basic import DependencyProvider
from autocrud.message_queue.simple import SimpleMessageQueueFactory
from autocrud.resource_manager.storage_factory import DiskStorageFactory
from cognee.api.v1.search import SearchType
from cognee.api.v1.visualize import visualize_graph
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from kb_api.cognee_mirror import CogneeMirrorHandler, configure_mirror
from kb_api.models import (
    ALL_MODELS,
    AgentFeedback,
    CaseStudy,
    DocumentSource,
    GlossaryEntry,
    RCAReport,
    Session,
)
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


# ─── AutoCRUD configuration (must run at module import, before app creation) ─

_AUTOCRUD_DATA_ROOT = Path("./data/autocrud").resolve()
_AUTOCRUD_DATA_ROOT.mkdir(parents=True, exist_ok=True)


def _configure_autocrud() -> None:
    """One-shot at module import. Registers all 6 models + cognee mirror handler."""
    crud.configure(
        storage_factory=DiskStorageFactory(str(_AUTOCRUD_DATA_ROOT)),
        message_queue_factory=SimpleMessageQueueFactory(),
        dependency_provider=DependencyProvider(
            get_user=lambda: "poc-admin",
            get_now=lambda: __import__("datetime").datetime.utcnow(),
        ),
        model_naming="kebab",
        encoding="json",
        event_handlers=[CogneeMirrorHandler()],
    )
    # Indexed fields chosen for QB filtering needs (status, owner, etc.).
    crud.add_model(CaseStudy, indexed_fields=[
        ("status", str), ("owner", str), ("defect_type", str),
        ("process_module", str),
    ])
    crud.add_model(Session, indexed_fields=[
        ("status", str), ("case_study_id", str), ("rca_completed", bool),
    ])
    crud.add_model(RCAReport, indexed_fields=[
        ("case_study_id", str), ("session_id", str), ("agreed", bool),
    ])
    crud.add_model(GlossaryEntry, indexed_fields=[
        ("term", str), ("source_session_id", str), ("source_case_study_id", str),
        ("confidence", str),
    ])
    crud.add_model(AgentFeedback, indexed_fields=[
        ("type", str), ("topic", str), ("source_session_id", str),
        ("source_case_study_id", str),
    ])
    crud.add_model(DocumentSource, indexed_fields=[
        ("source_kind", str), ("case_study_id", str), ("session_id", str),
    ])


_configure_autocrud()

# Side-effect import: registers Session open/close/abandon custom actions
# into the global `crud` instance via decorators. Must be after
# _configure_autocrud() (which calls add_model for Session) and before
# crud.apply(app) lower in this file.
from kb_api import session_actions  # noqa: E402,F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = load_settings()
    app.state.settings = settings
    app.state.cognee = CogneeClient(settings)
    app.state.pipeline = IngestionPipeline(settings)
    app.state.reasoner = CausalReasoner(settings, cognee_client=app.state.cognee)
    app.state.extractor = SemiconductorExtractor(settings)
    await app.state.cognee.setup()
    # Bind the cognee mirror — AutoCRUD events from now on push to cognee.
    configure_mirror(app.state.cognee, dataset="rca")
    logger.info("KB API ready (AutoCRUD + cognee mirror live)")
    yield


app = FastAPI(
    title="RCA Knowledge Base API",
    version="0.3.0",
    description=(
        "AutoCRUD = source of truth for typed records "
        "(CaseStudy / Session / RCAReport / GlossaryEntry / AgentFeedback / DocumentSource). "
        "Cognee = derived retrieval engine; receives mirrored text via event handler. "
        "Plus retain/recall endpoints for direct cognee access."
    ),
    lifespan=lifespan,
)

# Mount AutoCRUD's auto-generated routes (CRUD + search + revisions for all 6 models)
crud.apply(app)


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

def _node_set_for(source_kind: Literal["literature", "conversation", "rca_report"]) -> list[str]:
    """Map a source_kind to the cognee node_set used as a provenance marker.

    Trust hierarchy applied at recall time:
      rca_reports  > rca_conversations > rca_literature
    Reports are fab-validated outcomes; literature is textbook prior;
    conversations sit in between.
    """
    if source_kind == "rca_report":
        return ["rca_reports"]
    if source_kind == "conversation":
        return ["rca_conversations"]
    return ["rca_literature"]


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

    POC heuristic — each chunk carries its node_set name in the rendered text
    ("rca_literature", "rca_conversations", "rca_reports").
    """
    if source_filter == "all":
        return snippets
    if source_filter == "rca_reports":
        return [s for s in snippets if "rca_reports" in s]
    if source_filter == "conversations":
        return [s for s in snippets if "rca_conversations" in s]
    # literature: anything that isn't conversation or report
    return [
        s for s in snippets
        if "rca_conversations" not in s and "rca_reports" not in s
    ]


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
