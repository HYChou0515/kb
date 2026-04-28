"""Anthropic LLM adapter — implements ports.out.llm.LLMClient."""

from __future__ import annotations

import logging

from rca.config import Settings
from rca.ports.out.llm import Role

logger = logging.getLogger(__name__)


class AnthropicLLMAdapter:
    def __init__(self, settings: Settings, *, role: Role) -> None:
        from anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is unset")
        self.model = settings.extraction_model if role == "extraction" else settings.reasoning_model
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        logger.debug("Anthropic LLM adapter: model=%s role=%s", self.model, role)

    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
