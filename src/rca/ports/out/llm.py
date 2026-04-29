"""LLM outbound port — provider-agnostic completion contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

Role = Literal["extraction", "reasoning"]


class ILLMAdapter(ABC):
    """Minimal text-in / text-out completion contract.

    Implemented by adapter/out/llm/{openai,anthropic}.py. The `model`
    attribute is set by the adapter's ctor and exposes which concrete
    model/version is in use (useful for logging + swap-tests).
    """

    model: str

    @abstractmethod
    def complete(self, *, system: str, user: str, max_tokens: int) -> str: ...
