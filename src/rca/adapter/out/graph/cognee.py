"""Cognee graph adapter — implements ports.out.graph.IGraphAdapter.

Wires cognee's V1 add()+cognify() for batch-friendly ingestion and
cognee's V2 recall()/forget() for search and cleanup. cognee V2's
remember() bundles add+cognify per call — too expensive when a single
ingestion run pushes hundreds of chunks. We therefore stay on V1 add()
for the per-chunk path and keep cognify() exposed as an explicit batch
boundary on the port.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterable, Literal

import cognee

from rca.config import Settings
from rca.ports.out.graph import IGraphAdapter

logger = logging.getLogger(__name__)


class CogneeGraphAdapter(IGraphAdapter):
    """Lazy initializer for cognee — call `setup()` once before use."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ready = False

    async def setup(self) -> None:
        if self._ready:
            return
        self.settings.export_to_cognee_env()
        self.settings.cognee_data_root.mkdir(parents=True, exist_ok=True)
        self.settings.cognee_system_root.mkdir(parents=True, exist_ok=True)
        cognee.config.data_root_directory(str(self.settings.cognee_data_root))
        cognee.config.system_root_directory(str(self.settings.cognee_system_root))
        self._ready = True
        logger.info(
            "cognee initialized (graph=%s vector=%s)",
            self.settings.graph_db_provider,
            self.settings.vector_db_provider,
        )

    async def remember_text(
        self,
        text: str,
        *,
        dataset: str = "rca",
        node_set: list[str] | None = None,
    ) -> None:
        await self.setup()
        # V1 add() under the hood — defers cognify() so a batch of
        # remember_text() calls amortizes the graph build.
        await cognee.add(text, dataset_name=dataset, node_set=node_set)

    async def remember_files(
        self, paths: Iterable[Path], *, dataset: str = "rca"
    ) -> None:
        await self.setup()
        for p in paths:
            await cognee.add(str(p), dataset_name=dataset)

    async def cognify(self, *, dataset: str = "rca") -> None:
        await self.setup()
        await cognee.cognify([dataset])

    async def recall(
        self,
        query: str,
        *,
        search_type: Any = None,
        top_k: int = 10,
        node_set: list[str] | None = None,
        node_set_operator: Literal["AND", "OR"] = "OR",
    ) -> list[Any]:
        await self.setup()
        # cognee.recall() auto-routes when query_type is None; pass
        # explicit type when caller needs deterministic behavior.
        # node_set passes through cognee's RecallKwargs as node_name +
        # node_name_filter_operator — the SDK routes those into the
        # NodeSet filter on the retriever.
        kwargs: dict[str, Any] = {}
        if node_set:
            kwargs["node_name"] = node_set
            kwargs["node_name_filter_operator"] = node_set_operator
        return await cognee.recall(
            query_text=query,
            query_type=search_type,
            top_k=top_k,
            **kwargs,
        )

    async def forget(self) -> None:
        await self.setup()
        # cognee.forget(everything=True) replaces the legacy
        # prune.prune_data + prune.prune_system pair.
        await cognee.forget(everything=True)
        logger.warning("cognee data + graph + vectors forgotten")
