"""Local embedding server — wraps a sentence-transformers checkpoint with the
OpenAI ``/v1/embeddings`` API.

Why this exists: cognee 1.0's default embedding engine (``fastembed``) downloads
ONNX models from HuggingFace at first use, which is blocked in many enterprise
environments. cognee already supports ``EMBEDDING_PROVIDER=openai_compatible``
that talks to any OpenAI-compatible ``/v1/embeddings`` endpoint, so we just
expose your locally-downloaded sentence-transformers checkpoint behind one.

Run:
    uv run embedding-server
or:
    uv run python -m embedding_server.main

Configuration (env):
    LOCAL_EMBEDDING_MODEL_PATH      absolute path to the local ST checkpoint dir
    EMBEDDING_SERVER_HOST           default 127.0.0.1
    EMBEDDING_SERVER_PORT           default 8766
    EMBEDDING_DEVICE                cpu | cuda | cuda:N | mps   (default: auto)
    EMBEDDING_NORMALIZE             true | false                (default: true)
    EMBEDDING_MAX_SEQ_LEN           int, optional override of model's default
    EMBEDDING_BATCH_SIZE            int, default 32
    EMBEDDING_TRUST_REMOTE_CODE     true | false (default: true; required for some Qwen models)

After this server is running, point cognee at it via:
    EMBEDDING_PROVIDER=openai_compatible
    EMBEDDING_ENDPOINT=http://127.0.0.1:8766/v1
    EMBEDDING_MODEL=local-st       # any string; sent through but unused
    EMBEDDING_DIMENSIONS=<dim>     # must match the model
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _model_path() -> str:
    p = os.getenv("LOCAL_EMBEDDING_MODEL_PATH", "").strip()
    if not p:
        raise RuntimeError(
            "LOCAL_EMBEDDING_MODEL_PATH is not set. Point it at the directory "
            "containing your sentence-transformers checkpoint (e.g. /opt/models/qwen-embed)."
        )
    if not Path(p).exists():
        raise RuntimeError(f"LOCAL_EMBEDDING_MODEL_PATH does not exist: {p}")
    return p


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {raw!r}") from exc


def _resolve_device(spec: str) -> str:
    """auto → cuda if available else cpu. Otherwise pass through."""
    spec = (spec or "").strip().lower()
    if spec and spec != "auto":
        return spec
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Hard-disable any HuggingFace-side network access. Defence in depth: even
    # if the underlying model card or tokenizer tries to phone home (e.g. to
    # check for updates), this stops it.
    for k in ("TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "HF_HUB_OFFLINE"):
        os.environ.setdefault(k, "1")

    path = _model_path()
    device = _resolve_device(os.getenv("EMBEDDING_DEVICE", "auto"))
    trust_remote_code = _bool_env("EMBEDDING_TRUST_REMOTE_CODE", True)
    normalize = _bool_env("EMBEDDING_NORMALIZE", True)
    max_seq_len = _int_env("EMBEDDING_MAX_SEQ_LEN", None)
    batch_size = _int_env("EMBEDDING_BATCH_SIZE", 32) or 32

    from sentence_transformers import SentenceTransformer  # heavy import; defer

    logger.info(
        "Loading sentence-transformers from %s (device=%s, trust_remote_code=%s)",
        path,
        device,
        trust_remote_code,
    )
    model = SentenceTransformer(
        path, device=device, trust_remote_code=trust_remote_code
    )
    if max_seq_len is not None:
        model.max_seq_length = max_seq_len

    # sentence-transformers >=3.4 renamed get_sentence_embedding_dimension
    # to get_embedding_dimension. Use the new name with a runtime fallback
    # so this works on either version.
    if hasattr(model, "get_embedding_dimension"):
        dim = model.get_embedding_dimension()
    else:
        dim = model.get_sentence_embedding_dimension()
    app.state.model = model
    app.state.model_path = path
    app.state.dim = dim
    app.state.device = device
    app.state.normalize = normalize
    app.state.max_seq_length = model.max_seq_length
    app.state.batch_size = batch_size
    logger.info(
        "Embedding model ready. dim=%d, max_seq=%s, normalize=%s, batch=%d",
        dim,
        app.state.max_seq_length,
        normalize,
        batch_size,
    )
    yield


app = FastAPI(
    title="Local Embedding Server",
    version="0.1.0",
    description="OpenAI-compatible /v1/embeddings backed by a local sentence-transformers checkpoint.",
    lifespan=lifespan,
)


class EmbeddingRequest(BaseModel):
    input: list[str] | str = Field(..., description="One string or a list of strings")
    model: str | None = None
    encoding_format: str | None = "float"
    user: str | None = None


class EmbeddingItem(BaseModel):
    object: str = "embedding"
    embedding: list[float]
    index: int


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingItem]
    model: str
    usage: UsageInfo = UsageInfo()


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "model_path": getattr(app.state, "model_path", None),
        "dim": getattr(app.state, "dim", None),
        "device": getattr(app.state, "device", None),
        "max_seq_length": getattr(app.state, "max_seq_length", None),
        "normalize": getattr(app.state, "normalize", None),
        "batch_size": getattr(app.state, "batch_size", None),
    }


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings(req: EmbeddingRequest) -> EmbeddingResponse:
    if not hasattr(app.state, "model"):
        raise HTTPException(503, "Model not loaded yet")
    inputs = req.input if isinstance(req.input, list) else [req.input]
    if not inputs:
        raise HTTPException(400, "input is empty")

    model = app.state.model
    vectors = model.encode(
        inputs,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=app.state.normalize,
        batch_size=app.state.batch_size,
    )
    data = [EmbeddingItem(embedding=v.tolist(), index=i) for i, v in enumerate(vectors)]
    return EmbeddingResponse(data=data, model=req.model or "local-st")


def run() -> None:
    import uvicorn

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    host = os.getenv("EMBEDDING_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("EMBEDDING_SERVER_PORT", "8766"))
    uvicorn.run(
        "embedding_server.main:app",
        host=host,
        port=port,
        reload=False,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run()
