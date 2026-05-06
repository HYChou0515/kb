"""KB API — FastAPI entry. Wires the dep-injector Container, mounts AutoCRUD
auto-generated routes + the inbound APIRouters, registers custom actions.

Run:
    uv run uvicorn main:app --host 127.0.0.1 --port 8765 --reload

Or via the console script:
    uv run kb-api
"""

from __future__ import annotations

import logging
import traceback
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from rca.adapter.in_ import admin, recall, retain, workspace
from rca.container import container
from rca.services.workspace_lifecycle import cleanup_stale_active_sessions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = container.settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    graph = container.graph()
    await graph.setup()

    autocrud = container.autocrud()
    autocrud.register_actions()
    autocrud.apply(app)

    # Any Session record marked 'active' here is a leftover from a previous
    # kb-api process that died — the opencode subprocess it pointed at no
    # longer exists. Abandon them so the single-active-case constraint in
    # open_workspace doesn't 409 the user out of every fresh case open.
    await cleanup_stale_active_sessions(autocrud)

    # Eager-resolve so first-request latency doesn't include the full DI graph.
    # Routers fetch the same instance via Depends(get_kb) (rca.container).
    container.kb()

    # opencode runtime starts lazily on the first open-workspace call: its
    # project root is fixed at `opencode serve` startup, so we can't
    # meaningfully spawn it before we know which workspace dir to anchor to.
    # We still register a stop hook so the subprocess gets SIGTERM on
    # shutdown if it ever did spawn.
    opencode = container.opencode()

    logger.info("KB API ready (AutoCRUD wrapper + cognee mirror live)")
    try:
        yield
    finally:
        if hasattr(opencode, "stop"):
            await opencode.stop()


app = FastAPI(
    title="RCA Knowledge Base API",
    version="0.4.0",
    description=(
        "AutoCRUD = source of truth for typed records "
        "(CaseStudy / Session / RCAReport / GlossaryEntry / AgentFeedback / DocumentSource). "
        "Cognee = derived retrieval engine; receives mirrored text via event handler. "
        "RCAReport carries a 4-tier verification_status (manager-signoff trust layering, "
        "NOT physical experimental validation)."
    ),
    lifespan=lifespan,
)

app.include_router(admin.router)
app.include_router(retain.router)
app.include_router(recall.router)
app.include_router(workspace.router)


@app.exception_handler(Exception)
async def _verbose_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Surface internal errors as JSON instead of FastAPI's empty 500 body.

    Recognized upstream-LLM auth errors are mapped to 502 with a clear hint.
    """
    cls = exc.__class__.__name__
    msg = str(exc)
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


def run() -> None:  # console-script entry
    import uvicorn

    settings = container.settings()
    uvicorn.run(
        "rca.main:app",
        host=settings.kb_api_host,
        port=settings.kb_api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
