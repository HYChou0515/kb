"""Embedding outbound port — vector encoding contract.

Currently consumed by cognee internally via env-var-configured
openai_compatible endpoint, NOT by our Python services. This port exists
so future code (e.g. our own retrieval that bypasses cognee) can swap
embedding backends without touching consumers.
"""

from __future__ import annotations

from typing import Protocol

import msgspec


class EmbedRequest(msgspec.Struct):
    texts: list[str]
    model: str | None = None


class EmbedResponse(msgspec.Struct):
    vectors: list[list[float]]
    model: str
    dim: int


class EmbeddingClient(Protocol):
    async def embed(self, req: EmbedRequest) -> EmbedResponse: ...

    async def health(self) -> dict: ...
