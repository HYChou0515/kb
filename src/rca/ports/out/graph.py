"""Graph outbound port — knowledge graph + retrieval contract.

Surface matches cognee's API today; impl (CogneeGraphAdapter) lives in
adapter/out/graph/cognee.py. Future swaps (LightRAG, self-hosted Neo4j+)
implement this Protocol.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Protocol


class GraphClient(Protocol):
    async def setup(self) -> None: ...

    async def add_text(
        self,
        text: str,
        *,
        dataset: str = "rca",
        node_set: list[str] | None = None,
    ) -> None: ...

    async def add_documents(
        self, paths: Iterable[Path], *, dataset: str = "rca"
    ) -> None: ...

    async def cognify(self, *, dataset: str = "rca") -> None: ...

    async def search(
        self,
        query: str,
        *,
        search_type: Any = ...,
        top_k: int = 10,
    ) -> list[Any]: ...

    async def prune(self) -> None: ...
