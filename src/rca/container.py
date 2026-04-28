"""Dependency-injector container — wires everything from Settings down.

All consumers (services, adapter/in_ routers, MCP server) resolve their
deps via this container. Tests can override providers to inject fakes
(e.g. `container.graph.override(FakeGraph())`) without touching consumer
code.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from rca.adapter.out.autocrud.cognee_mirror import CogneeMirrorHandler
from rca.adapter.out.autocrud.wrapper import AutoCrudWrapper
from rca.adapter.out.embedding.local_http import LocalHTTPEmbeddingAdapter
from rca.adapter.out.graph.cognee import CogneeGraphAdapter
from rca.adapter.out.llm.anthropic import AnthropicLLMAdapter
from rca.adapter.out.llm.openai import OpenAILLMAdapter
from rca.config import Settings, load_settings
from rca.services.extraction import SemiconductorExtractionService
from rca.services.ingestion import IngestionPipelineService
from rca.services.kb import KBService
from rca.services.reasoning import CausalReasoningService


class Container(containers.DeclarativeContainer):
    settings: providers.Provider[Settings] = providers.Singleton(load_settings)

    _llm_provider_key = providers.Callable(
        lambda s: s.llm_provider, settings
    )

    extraction_llm = providers.Selector(
        _llm_provider_key,
        openai=providers.Singleton(OpenAILLMAdapter, settings=settings, role="extraction"),
        anthropic=providers.Singleton(AnthropicLLMAdapter, settings=settings, role="extraction"),
    )

    reasoning_llm = providers.Selector(
        _llm_provider_key,
        openai=providers.Singleton(OpenAILLMAdapter, settings=settings, role="reasoning"),
        anthropic=providers.Singleton(AnthropicLLMAdapter, settings=settings, role="reasoning"),
    )

    graph = providers.Singleton(CogneeGraphAdapter, settings=settings)

    embedding = providers.Singleton(LocalHTTPEmbeddingAdapter, settings=settings)

    cognee_mirror = providers.Singleton(
        CogneeMirrorHandler, graph=graph, dataset="rca"
    )

    autocrud = providers.Singleton(
        AutoCrudWrapper, settings=settings, mirror=cognee_mirror
    )

    extraction = providers.Singleton(
        SemiconductorExtractionService, llm=extraction_llm
    )

    ingestion = providers.Singleton(
        IngestionPipelineService, extractor=extraction, graph=graph
    )

    reasoning = providers.Singleton(
        CausalReasoningService, llm=reasoning_llm, graph=graph
    )

    kb = providers.Singleton(
        KBService,
        ingestion=ingestion,
        reasoning=reasoning,
        extraction=extraction,
        autocrud=autocrud,
        graph=graph,
    )
