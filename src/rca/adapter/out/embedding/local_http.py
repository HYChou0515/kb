"""Local-HTTP embedding adapter — calls the in-process embedding-server.

Implements ports.out.embedding.IEmbeddingAdapter. Currently no service in
this codebase consumes embeddings directly (cognee handles its own via
EMBEDDING_PROVIDER=openai_compatible env vars). This adapter exists as
the swap point for future code that wants embeddings without going
through cognee.
"""

from __future__ import annotations

import logging

import httpx

from rca.config import Settings
from rca.ports.out.embedding import EmbedRequest, EmbedResponse, IEmbeddingAdapter

logger = logging.getLogger(__name__)


class LocalHTTPEmbeddingAdapter(IEmbeddingAdapter):
    def __init__(self, settings: Settings) -> None:
        self.endpoint = settings.embedding_endpoint.rstrip("/")
        self.default_model = settings.embedding_model
        self.api_key = settings.embedding_api_key
        self.dim = settings.embedding_dimensions

    async def embed(self, req: EmbedRequest) -> EmbedResponse:
        headers = {}
        if self.api_key and self.api_key != "no-key-required":
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as c:
            r = await c.post(
                f"{self.endpoint}/embeddings",
                headers=headers,
                json={
                    "input": req.texts,
                    "model": req.model or self.default_model,
                },
            )
            r.raise_for_status()
            data = r.json()
        vectors = [item["embedding"] for item in data["data"]]
        return EmbedResponse(
            vectors=vectors,
            model=data.get("model", self.default_model),
            dim=len(vectors[0]) if vectors else self.dim,
        )

    async def health(self) -> dict:
        base = self.endpoint
        if base.endswith("/v1"):
            base = base[: -len("/v1")]
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as c:
            r = await c.get(f"{base}/health")
            r.raise_for_status()
            return r.json()
