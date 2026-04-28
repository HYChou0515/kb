"""LLM outbound port — provider-agnostic completion contract."""

from __future__ import annotations

from typing import Literal, Protocol

Role = Literal["extraction", "reasoning"]


class LLMClient(Protocol):
    """Minimal text-in / text-out completion contract.

    Implemented by adapter/out/llm/{openai,anthropic}.py.
    """

    model: str

    def complete(self, *, system: str, user: str, max_tokens: int) -> str: ...
