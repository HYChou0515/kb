"""Provider-agnostic LLM client for KB extraction and reasoning.

Wraps Anthropic and OpenAI behind a single `complete(system, user)` method
that returns the assistant's text. Cognee handles its own LLM calls via
LiteLLM (controlled by LLM_PROVIDER env vars).

Usage:
    from rca_knowledge.llm import make_llm_client

    client = make_llm_client(settings, role="extraction")
    text = client.complete(system=SYSTEM_PROMPT, user=user_msg, max_tokens=8000)
"""

from __future__ import annotations

import logging
from typing import Literal, Protocol

from rca_knowledge.config import Settings

logger = logging.getLogger(__name__)

Role = Literal["extraction", "reasoning"]


class LLMClient(Protocol):
    """Minimal text-in / text-out completion contract."""

    model: str

    def complete(self, *, system: str, user: str, max_tokens: int) -> str: ...


class _AnthropicClient:
    def __init__(self, api_key: str, model: str) -> None:
        from anthropic import Anthropic  # local import: keeps OpenAI-only deploys lean

        self._client = Anthropic(api_key=api_key)
        self.model = model

    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


class _OpenAIClient:
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        # response_format=json_object would be ideal, but our prompts ask for
        # strict JSON without enforcement so callers can also use this client
        # for free-text reasoning. The reasoner/extractor strip code fences
        # if the model wraps JSON in ```...```.
        resp = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = resp.choices[0]
        return choice.message.content or ""


def make_llm_client(settings: Settings, *, role: Role) -> LLMClient:
    """Return a configured client for the given role.

    Both extraction and reasoning currently share the same provider; the role
    parameter is here so we can split them later (e.g. cheaper model for
    extraction) without rewriting callers.
    """
    model = settings.extraction_model if role == "extraction" else settings.reasoning_model
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is unset")
        logger.debug("LLM client: anthropic / %s (role=%s)", model, role)
        return _AnthropicClient(api_key=settings.anthropic_api_key, model=model)
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is unset")
        logger.debug("LLM client: openai / %s (role=%s)", model, role)
        return _OpenAIClient(api_key=settings.openai_api_key, model=model)
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
