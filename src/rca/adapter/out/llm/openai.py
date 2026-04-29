"""OpenAI LLM adapter — implements ports.out.llm.ILLMAdapter."""

from __future__ import annotations

import logging

from rca.config import Settings
from rca.ports.out.llm import ILLMAdapter, Role

logger = logging.getLogger(__name__)


class OpenAILLMAdapter(ILLMAdapter):
    def __init__(self, settings: Settings, *, role: Role) -> None:
        from openai import OpenAI

        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is unset")
        self.model = (
            settings.extraction_model
            if role == "extraction"
            else settings.reasoning_model
        )
        self._client = OpenAI(api_key=settings.openai_api_key)
        logger.debug("OpenAI LLM adapter: model=%s role=%s", self.model, role)

    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
