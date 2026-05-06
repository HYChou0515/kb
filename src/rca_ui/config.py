"""rca_ui configuration. Reads env once at process start.

Only the bits rca_ui actually needs — port, kb-api URL, LLM model for the
agent, paths. Falls back to the LLM_* / OPENCODE_LLM_* / KB_API_* names
already used by kb-api so a single .env serves both processes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default) or default


_DEFAULT_MODEL_BY_PROVIDER = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-5",
}


@dataclass(frozen=True)
class UISettings:
    ui_host: str
    ui_port: int

    kb_api_base_url: str

    llm_provider: str
    llm_model: str
    openai_api_key: str
    anthropic_api_key: str

    workspace_root: Path

    # Path to npx; null/missing means we rely on PATH lookup at spawn time.
    npx_bin: str

    @property
    def llm_provider_model(self) -> str:
        """OpenAI Agents SDK accepts `<provider>/<model>` strings via the
        litellm extra. For pure OpenAI we just pass the model id."""
        if self.llm_provider == "openai":
            return self.llm_model
        return f"litellm/{self.llm_provider}/{self.llm_model}"


def load_ui_settings() -> UISettings:
    provider = _env("RCA_UI_LLM_PROVIDER", _env("LLM_PROVIDER", "openai")).lower()
    if provider not in _DEFAULT_MODEL_BY_PROVIDER:
        raise RuntimeError(
            f"Unsupported RCA_UI_LLM_PROVIDER/LLM_PROVIDER: {provider!r}"
        )

    model = (
        _env("RCA_UI_LLM_MODEL", "")
        or _env("OPENCODE_LLM_MODEL", "")
        or _env("LLM_MODEL", _DEFAULT_MODEL_BY_PROVIDER[provider])
    )

    openai_key = _env("OPENAI_API_KEY", "")
    anthropic_key = _env("ANTHROPIC_API_KEY", "")
    if provider == "openai" and not openai_key:
        raise RuntimeError(
            "RCA_UI_LLM_PROVIDER=openai but OPENAI_API_KEY is not set."
        )
    if provider == "anthropic" and not anthropic_key:
        raise RuntimeError(
            "RCA_UI_LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set."
        )

    return UISettings(
        ui_host=_env("RCA_UI_HOST", "127.0.0.1"),
        ui_port=int(_env("RCA_UI_PORT", "3001")),
        kb_api_base_url=_env("KB_API_BASE_URL", "http://127.0.0.1:8765"),
        llm_provider=provider,
        llm_model=model,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        workspace_root=Path(
            _env("RCA_UI_WORKSPACE_ROOT", str(PROJECT_ROOT / "data" / "workspaces"))
        ).resolve(),
        npx_bin=_env("NPX_BIN", "npx"),
    )
