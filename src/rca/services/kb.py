"""KBService — application service orchestrator (inbound port impl).

FastAPI routes and the in-process MCP adapter both delegate here. Holds the
wired services (ingestion, reasoning, extraction) plus the AutoCRUD
wrapper for typed AutoCRUD-backed report ops, and the IGraphAdapter for
direct-to-graph operations like cognify / prune.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from rca.ports.in_.admin import CognifyRequest, StatusResponse
from rca.ports.in_.recall import (
    RecallAssessmentResponse,
    RecallRequest,
    RecallSnippetsResponse,
    RecallSynthesisResponse,
)
from rca.ports.in_.retain import (
    RetainConversationRequest,
    RetainExtractionRequest,
    RetainResponse,
    RetainTextRequest,
)
from rca.ports.out.autocrud import IAutoCrudWrapper
from rca.ports.out.graph import IGraphAdapter
from rca.services.extraction import IExtractionService, render_extraction_for_cognee
from rca.services.ingestion import IIngestionService, IngestedChunk
from rca.services.reasoning import IReasoningService

logger = logging.getLogger(__name__)


SourceKind = Literal["literature", "conversation", "rca_report"]


def _node_set_for(source_kind: SourceKind) -> list[str]:
    """Map a source_kind to the cognee node_set provenance marker."""
    if source_kind == "rca_report":
        return ["rca_reports"]
    if source_kind == "conversation":
        return ["rca_conversations"]
    return ["rca_literature"]


def _summarize_chunks(chunks: list[IngestedChunk]) -> RetainResponse:
    n_e = sum(len(c.extraction.entities) for c in chunks)
    n_r = sum(len(c.extraction.relations) for c in chunks)
    summaries = [c.extraction.summary for c in chunks if c.extraction.summary]
    return RetainResponse(
        chunks_ingested=len(chunks),
        entities_extracted=n_e,
        relations_extracted=n_r,
        summary=" | ".join(summaries[:3]),
        source_labels=[c.source_label for c in chunks],
    )


def _filter_by_source(snippets: list[str], source_filter: str) -> list[str]:
    if source_filter == "all":
        return snippets
    if source_filter == "rca_reports":
        return [s for s in snippets if "rca_reports" in s]
    if source_filter == "conversations":
        return [s for s in snippets if "rca_conversations" in s]
    return [
        s for s in snippets if "rca_conversations" not in s and "rca_reports" not in s
    ]


def _filter_refuted(snippets: list[str]) -> list[str]:
    return [s for s in snippets if "rca_reports_refuted" not in s]


class IKBService(ABC):
    @abstractmethod
    async def retain_text(self, req: RetainTextRequest) -> RetainResponse: ...

    @abstractmethod
    async def retain_conversation(
        self, req: RetainConversationRequest
    ) -> RetainResponse: ...

    @abstractmethod
    async def retain_extraction(
        self, req: RetainExtractionRequest
    ) -> RetainResponse: ...

    @abstractmethod
    async def retain_file(
        self,
        path: Path,
        *,
        label: str | None,
        dataset: str,
        cognify: bool,
        source_kind: SourceKind,
    ) -> RetainResponse: ...

    @abstractmethod
    async def recall(
        self, req: RecallRequest
    ) -> (
        RecallSnippetsResponse | RecallAssessmentResponse | RecallSynthesisResponse
    ): ...

    @abstractmethod
    async def admin_cognify(self, req: CognifyRequest) -> StatusResponse: ...

    @abstractmethod
    async def admin_prune(self) -> StatusResponse: ...

    @abstractmethod
    async def visualize_graph(self) -> str: ...


class KBService(IKBService):
    def __init__(
        self,
        ingestion: IIngestionService,
        reasoning: IReasoningService,
        extraction: IExtractionService,
        autocrud: IAutoCrudWrapper,
        graph: IGraphAdapter,
    ) -> None:
        self.ingestion = ingestion
        self.reasoning = reasoning
        self.extraction = extraction
        self.autocrud = autocrud
        self.graph = graph

    async def retain_text(self, req: RetainTextRequest) -> RetainResponse:
        chunks = await self.ingestion.ingest_text(
            req.text,
            source_label=req.label,
            dataset=req.dataset,
            node_set=_node_set_for(req.source_kind),
            run_cognify=req.cognify,
        )
        return _summarize_chunks(chunks)

    async def retain_conversation(
        self, req: RetainConversationRequest
    ) -> RetainResponse:
        chunks = await self.ingestion.ingest_conversation(
            req.messages,
            session_id=req.session_id,
            dataset=req.dataset,
            run_cognify=req.cognify,
        )
        return _summarize_chunks(chunks)

    async def retain_extraction(self, req: RetainExtractionRequest) -> RetainResponse:
        rendered = render_extraction_for_cognee(
            req.extraction, source_label=req.source_label
        )
        await self.graph.remember_text(
            rendered, dataset=req.dataset, node_set=_node_set_for(req.source_kind)
        )
        if req.cognify:
            await self.graph.cognify(dataset=req.dataset)

        return RetainResponse(
            chunks_ingested=1,
            entities_extracted=len(req.extraction.entities),
            relations_extracted=len(req.extraction.relations),
            summary=req.extraction.summary,
            source_labels=[req.source_label],
        )

    async def retain_file(
        self,
        path: Path,
        *,
        label: str | None,
        dataset: str,
        cognify: bool,
        source_kind: SourceKind,
    ) -> RetainResponse:
        chunks = await self.ingestion.ingest_file(
            path,
            dataset=dataset,
            node_set=_node_set_for(source_kind),
            run_cognify=cognify,
        )
        resp = _summarize_chunks(chunks)
        if label:
            resp.source_labels = [f"{label}:{s}" for s in resp.source_labels]
        return resp

    async def recall(
        self, req: RecallRequest
    ) -> RecallSnippetsResponse | RecallAssessmentResponse | RecallSynthesisResponse:
        if req.mode == "snippets":
            snippets = await self.reasoning.retrieve_context(
                req.query, req.process_context, top_k=req.top_k
            )
            snippets = _filter_by_source(snippets, req.source_filter)
            if req.exclude_refuted:
                snippets = _filter_refuted(snippets)
            return RecallSnippetsResponse(snippets=snippets[: req.top_k])

        if req.mode == "assessment":
            assessment = await self.reasoning.assess(
                req.query,
                process_context=req.process_context,
                top_k=req.top_k,
            )
            return RecallAssessmentResponse(assessment=assessment)

        if req.mode == "synthesis":
            from cognee.api.v1.search import SearchType

            results = await self.graph.recall(
                req.query,
                search_type=SearchType.GRAPH_COMPLETION,
                top_k=req.top_k,
            )
            text_results: list[str] = [str(r) for r in results]
            synthesis = (
                "\n\n".join(text_results) if text_results else "(no graph match)"
            )
            return RecallSynthesisResponse(synthesis=synthesis, raw=text_results)

        raise ValueError(f"unknown mode: {req.mode}")

    async def admin_cognify(self, req: CognifyRequest) -> StatusResponse:
        await self.graph.cognify(dataset=req.dataset)
        return StatusResponse(ok=True, detail=f"cognify(dataset={req.dataset}) done")

    async def admin_prune(self) -> StatusResponse:
        await self.graph.forget()
        return StatusResponse(ok=True, detail="cognee stores pruned")

    async def visualize_graph(self) -> str:
        """Render the entire knowledge graph as standalone HTML. Cognee-
        specific helper isolated here so the admin router stays thin and
        the IKBService contract owns this capability."""
        from cognee.api.v1.visualize import visualize_graph as _viz

        await self.graph.setup()
        return await _viz()
