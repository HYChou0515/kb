"""Dependency-injector container — wires everything from Settings down.

All consumers (services, adapter/in_ routers, MCP server) resolve their
deps via this container. Tests can override providers to inject fakes
(e.g. `container.graph.override(FakeGraph())`) without touching consumer
code.

Provider attributes are annotated with `providers.Provider[IFoo]` (the
ABC interface, not the concrete adapter class) so static type checkers
verify swap-correctness at the wiring site, and `.override(fake)` works
type-safely in tests.
"""

from __future__ import annotations

from autocrud.types import IEventHandler
from dependency_injector import containers, providers

from rca.adapter.out.autocrud.cognee_mirror import CogneeMirrorHandler
from rca.adapter.out.autocrud.wrapper import AutoCrudWrapper
from rca.adapter.out.embedding.local_http import LocalHTTPEmbeddingAdapter
from rca.adapter.out.graph.cognee import CogneeGraphAdapter
from rca.adapter.out.llm.anthropic import AnthropicLLMAdapter
from rca.adapter.out.llm.openai import OpenAILLMAdapter
from rca.config import Settings, load_settings
from rca.ports.out.autocrud import IAutoCrudWrapper
from rca.ports.out.embedding import IEmbeddingAdapter
from rca.ports.out.graph import IGraphAdapter
from rca.ports.out.llm import ILLMAdapter
from rca.services.extraction import IExtractionService, SemiconductorExtractionService
from rca.services.ingestion import IIngestionService, IngestionPipelineService
from rca.services.kb import IKBService, KBService
from rca.services.reasoning import CausalReasoningService, IReasoningService


class Container(containers.DeclarativeContainer):
    settings: providers.Provider[Settings] = providers.Singleton(load_settings)

    _llm_provider_key = providers.Callable(lambda s: s.llm_provider, settings)

    extraction_llm: providers.Provider[ILLMAdapter] = providers.Selector(
        _llm_provider_key,
        openai=providers.Singleton(
            OpenAILLMAdapter, settings=settings, role="extraction"
        ),
        anthropic=providers.Singleton(
            AnthropicLLMAdapter, settings=settings, role="extraction"
        ),
    )

    reasoning_llm: providers.Provider[ILLMAdapter] = providers.Selector(
        _llm_provider_key,
        openai=providers.Singleton(
            OpenAILLMAdapter, settings=settings, role="reasoning"
        ),
        anthropic=providers.Singleton(
            AnthropicLLMAdapter, settings=settings, role="reasoning"
        ),
    )

    graph: providers.Provider[IGraphAdapter] = providers.Singleton(
        CogneeGraphAdapter, settings=settings
    )

    embedding: providers.Provider[IEmbeddingAdapter] = providers.Singleton(
        LocalHTTPEmbeddingAdapter, settings=settings
    )

    cognee_mirror: providers.Provider[IEventHandler] = providers.Singleton(
        CogneeMirrorHandler, graph=graph, dataset="rca"
    )

    autocrud: providers.Provider[IAutoCrudWrapper] = providers.Singleton(
        AutoCrudWrapper, settings=settings, mirror=cognee_mirror
    )

    extraction: providers.Provider[IExtractionService] = providers.Singleton(
        SemiconductorExtractionService, llm=extraction_llm
    )

    ingestion: providers.Provider[IIngestionService] = providers.Singleton(
        IngestionPipelineService, extractor=extraction, graph=graph
    )

    reasoning: providers.Provider[IReasoningService] = providers.Singleton(
        CausalReasoningService, llm=reasoning_llm, graph=graph
    )

    kb: providers.Provider[IKBService] = providers.Singleton(
        KBService,
        ingestion=ingestion,
        reasoning=reasoning,
        extraction=extraction,
        autocrud=autocrud,
        graph=graph,
    )


# ─── module-level singleton + FastAPI Depends helpers ─────────────────────
# Routers and the in-process MCP server import these instead of fishing
# the kb instance out of `request.app.state.kb` (which Pylance treats as
# an opaque dynamic attribute and can't type-check).
#
# Tests override providers via `container.kb.override(fake_kb)`, so the
# helpers below resolve the override transparently.

container = Container()


def get_kb() -> IKBService:
    return container.kb()
