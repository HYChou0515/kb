"""Cognee graph adapter — implements ports.out.graph.GraphClient."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterable

import cognee
from cognee.api.v1.search import SearchType

from rca.config import Settings

logger = logging.getLogger(__name__)


class CogneeGraphAdapter:
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

    async def add_text(
        self,
        text: str,
        *,
        dataset: str = "rca",
        node_set: list[str] | None = None,
    ) -> None:
        await self.setup()
        await cognee.add(text, dataset_name=dataset, node_set=node_set)

    async def add_documents(
        self, paths: Iterable[Path], *, dataset: str = "rca"
    ) -> None:
        await self.setup()
        for p in paths:
            await cognee.add(str(p), dataset_name=dataset)

    async def cognify(self, *, dataset: str = "rca") -> None:
        await self.setup()
        await cognee.cognify([dataset])

    async def search(
        self,
        query: str,
        *,
        search_type: Any = SearchType.GRAPH_COMPLETION,
        top_k: int = 10,
    ) -> list[Any]:
        await self.setup()
        return await cognee.search(
            query_text=query,
            query_type=search_type,
            top_k=top_k,
        )

    async def prune(self) -> None:
        await self.setup()
        await cognee.prune.prune_data()
        await cognee.prune.prune_system(metadata=True)
        logger.warning("cognee stores pruned")
