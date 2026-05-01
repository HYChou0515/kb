"""Sanity-check the configured LLM provider key with a tiny call.

Exits 0 if the provider answered, non-zero with a clear error otherwise.
Used by demo.sh to fail fast before booting the KB API.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca.config import load_settings  # noqa: E402


def main() -> int:
    try:
        settings = load_settings()
    except Exception as exc:
        print(f"FAIL: config load → {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"  provider: {settings.llm_provider}")
    print(f"  model:    {settings.llm_model}")

    # Instantiate the LLM adapter directly instead of going through the DI
    # Container — Container imports the cognee graph adapter eagerly, and a
    # key sanity check shouldn't pay cognee's startup cost (or pollute logs).
    try:
        if settings.llm_provider == "openai":
            from rca.adapter.out.llm.openai import OpenAILLMAdapter

            client = OpenAILLMAdapter(settings=settings, role="reasoning")
        else:
            from rca.adapter.out.llm.anthropic import AnthropicLLMAdapter

            client = AnthropicLLMAdapter(settings=settings, role="reasoning")
        out = client.complete(system="Reply with the single word OK.", user="ping", max_tokens=10)
    except Exception as exc:
        cls = exc.__class__.__name__
        print(f"FAIL: {cls}: {exc}", file=sys.stderr)
        if "AuthenticationError" in cls or "incorrect api key" in str(exc).lower():
            print(
                "Hint: the LLM provider rejected the key. Common causes:\n"
                "  • Extra quotes or trailing whitespace in .env\n"
                "  • Key revoked / project lacks access to the model\n"
                "  • Mixing OpenAI vs Anthropic key with the wrong LLM_PROVIDER",
                file=sys.stderr,
            )
        return 1

    print(f"  reply:    {out.strip()[:60]}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
