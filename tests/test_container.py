"""Container — DI graph integrity.

The dep-injector Container is the load-bearing wiring layer of the refactor.
If Container().kb() can be resolved without errors, every adapter, port, and
service constructor was correctly typed and the providers correctly chained.

We don't actually CALL the resolved services (those would hit real cognee /
OpenAI). We just resolve and assert types — the wiring is what matters.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _set_env(monkeypatch: pytest.MonkeyPatch, *, provider: str, tmp_path: Path) -> None:
    """Set the minimum env vars for load_settings() to succeed."""
    if provider == "openai":
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test-key")
    elif provider == "anthropic":
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test-key")
    monkeypatch.setenv("AUTOCRUD_DATA_ROOT", str(tmp_path / "autocrud"))
    monkeypatch.setenv("COGNEE_DATA_ROOT", str(tmp_path / "cognee_data"))
    monkeypatch.setenv("COGNEE_SYSTEM_ROOT", str(tmp_path / "cognee_system"))


def test_container_resolves_full_kb_graph(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The whole DI graph (settings → outbound adapters → services → KBService)
    resolves without missing dependencies, type errors, or import failures.

    This is the load-bearing test for the entire refactor: if it passes, every
    adapter implements the corresponding port shape correctly enough that
    services can take it via constructor injection."""
    _set_env(monkeypatch, provider="openai", tmp_path=tmp_path)

    from rca.container import Container
    from rca.services.kb import KBService

    container = Container()
    kb = container.kb()
    assert isinstance(kb, KBService)

    # Same singleton graph instance shared between services — eliminating the
    # duplicate `CogneeClient(settings)` construction that the legacy code had.
    assert container.graph() is container.graph()
    assert kb.graph is container.graph()


@pytest.mark.parametrize(
    "provider,expected_class",
    [
        ("openai", "OpenAILLMAdapter"),
        ("anthropic", "AnthropicLLMAdapter"),
    ],
)
def test_llm_selector_switches_on_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    provider: str,
    expected_class: str,
) -> None:
    """The LLM Selector resolves to the adapter matching settings.llm_provider.
    This is the heart of the "swap infra easily" goal — flipping LLM_PROVIDER
    in env between openai and anthropic gives a different adapter class with
    no consumer-side change."""
    _set_env(monkeypatch, provider=provider, tmp_path=tmp_path)

    from rca.container import Container

    container = Container()
    extraction_llm = container.extraction_llm()
    reasoning_llm = container.reasoning_llm()

    assert type(extraction_llm).__name__ == expected_class
    assert type(reasoning_llm).__name__ == expected_class

    # Roles get distinct models — a `extraction_model` env var (or the same
    # default) is read at adapter construction; the ILLMAdapter.model attribute
    # is the externally-visible witness of the role split.
    assert hasattr(extraction_llm, "model")
    assert hasattr(reasoning_llm, "model")
