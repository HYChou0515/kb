"""Graph outbound port — knowledge graph + retrieval contract.

Surface aligned with cognee's V2 memory-oriented API (remember / recall /
forget). The implementation in adapter/out/graph/cognee.py uses cognee
V2 functions for recall/forget, and keeps cognee V1 add()+cognify() for
the batch-friendly ingestion path (so a long stream of remember_text()
calls can be cognified together at the end instead of per-chunk).

Future swaps (LightRAG, self-hosted Neo4j+) implement this ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, Literal


class IGraphAdapter(ABC):
    @abstractmethod
    async def setup(self) -> None: ...

    @abstractmethod
    async def remember_text(
        self,
        text: str,
        *,
        dataset: str = "rca",
        node_set: list[str] | None = None,
    ) -> None:
        """Ingest a single text chunk into the graph dataset.

        Heavy lifting (cognify) is deferred — call cognify() once after
        a batch of remember_text() calls."""
        ...

    @abstractmethod
    async def remember_files(
        self, paths: Iterable[Path], *, dataset: str = "rca"
    ) -> None: ...

    @abstractmethod
    async def cognify(self, *, dataset: str = "rca") -> None:
        """Build the knowledge graph for the dataset. Run after a batch
        of remember_text/remember_files calls."""
        ...

    @abstractmethod
    async def recall(
        self,
        query: str,
        *,
        search_type: Any = None,
        top_k: int = 10,
        node_set: list[str] | None = None,
        node_set_operator: Literal["AND", "OR"] = "OR",
    ) -> list[Any]:
        """Retrieve from the graph. With search_type=None the underlying
        engine auto-routes by query intent.

        When `node_set` is provided, results are filtered to chunks tagged
        with at least one (OR) or all (AND) of the listed node_set names —
        matches the tags written via remember_text(node_set=...). This is
        the load-bearing knob for status-aware retrieval (the reasoner
        passes node_set=["rca_reports_verified"] to weight by manager
        signoff trust)."""
        ...

    @abstractmethod
    async def forget(self) -> None:
        """Drop ALL data + graph + vectors. Destructive."""
        ...
