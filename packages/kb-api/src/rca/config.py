"""Minimal kb-api configuration.

Only what the thin proxy needs: HTTP host/port, log level, and the env
vars cognee reads at runtime (LLM provider, embedding endpoint, data dirs).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# In the workspace layout this file is at:
#   <workspace>/packages/kb-api/src/rca/config.py
# parents: [0]=rca, [1]=src, [2]=kb-api, [3]=packages, [4]=workspace
PROJECT_ROOT = Path(__file__).resolve().parents[4]

load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val or ""


def _eager_export_cognee_paths() -> None:
    """Set cognee data dirs before any cognee module imports — cognee's
    logger initializes against them at import time, so a late override
    leaves a misleading 'Database storage: <site-packages>/...' line in
    early logs."""
    data_root = Path(
        os.environ.get("COGNEE_DATA_ROOT") or str(PROJECT_ROOT / ".cognee_data")
    ).resolve()
    system_root = Path(
        os.environ.get("COGNEE_SYSTEM_ROOT") or str(PROJECT_ROOT / ".cognee_system")
    ).resolve()
    os.environ.setdefault("DATA_ROOT_DIRECTORY", str(data_root))
    os.environ.setdefault("SYSTEM_ROOT_DIRECTORY", str(system_root))


_eager_export_cognee_paths()


@dataclass(frozen=True)
class Settings:
    kb_api_host: str
    kb_api_port: int
    log_level: str

    # Forwarded into cognee's process env on startup. cognee picks them
    # up via its own env reader (LiteLLM under the hood).
    llm_provider: str
    llm_model: str
    llm_api_key: str
    openai_api_key: str
    anthropic_api_key: str

    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    embedding_endpoint: str
    embedding_api_key: str

    cognee_data_root: Path
    cognee_system_root: Path
    graph_db_provider: str
    vector_db_provider: str

    def export_to_cognee_env(self) -> None:
        os.environ["LLM_PROVIDER"] = self.llm_provider
        os.environ["LLM_MODEL"] = self.llm_model
        os.environ["LLM_API_KEY"] = self.llm_api_key
        os.environ["EMBEDDING_PROVIDER"] = self.embedding_provider
        os.environ["EMBEDDING_MODEL"] = self.embedding_model
        os.environ["EMBEDDING_DIMENSIONS"] = str(self.embedding_dimensions)
        if self.embedding_endpoint:
            os.environ["EMBEDDING_ENDPOINT"] = self.embedding_endpoint
        if self.embedding_api_key:
            os.environ["EMBEDDING_API_KEY"] = self.embedding_api_key
        os.environ["GRAPH_DATABASE_PROVIDER"] = self.graph_db_provider
        os.environ["VECTOR_DB_PROVIDER"] = self.vector_db_provider
        os.environ["DATA_ROOT_DIRECTORY"] = str(self.cognee_data_root)
        os.environ["SYSTEM_ROOT_DIRECTORY"] = str(self.cognee_system_root)
        os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
        if self.openai_api_key:
            os.environ.setdefault("OPENAI_API_KEY", self.openai_api_key)
        if self.anthropic_api_key:
            os.environ.setdefault("ANTHROPIC_API_KEY", self.anthropic_api_key)


def load_settings() -> Settings:
    provider = _env("LLM_PROVIDER", "openai").lower()
    if provider not in {"openai", "anthropic"}:
        raise RuntimeError(
            f"Unsupported LLM_PROVIDER: {provider!r}. Use 'openai' or 'anthropic'."
        )

    openai_key = _env("OPENAI_API_KEY", "")
    anthropic_key = _env("ANTHROPIC_API_KEY", "")
    if provider == "openai" and not openai_key:
        raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set.")
    if provider == "anthropic" and not anthropic_key:
        raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set.")

    active_key = openai_key if provider == "openai" else anthropic_key
    default_model = "gpt-4o" if provider == "openai" else "claude-sonnet-4-5"

    return Settings(
        kb_api_host=_env("KB_API_HOST", "127.0.0.1"),
        kb_api_port=int(_env("KB_API_PORT", "8765")),
        log_level=_env("LOG_LEVEL", "INFO"),
        llm_provider=provider,
        llm_model=_env("LLM_MODEL", default_model),
        llm_api_key=_env("LLM_API_KEY", active_key),
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        embedding_provider=_env("EMBEDDING_PROVIDER", "openai_compatible"),
        embedding_model=_env("EMBEDDING_MODEL", "local-st"),
        embedding_dimensions=int(_env("EMBEDDING_DIMENSIONS", "1024")),
        embedding_endpoint=_env("EMBEDDING_ENDPOINT", "http://127.0.0.1:8766/v1"),
        embedding_api_key=_env("EMBEDDING_API_KEY", "no-key-required"),
        cognee_data_root=Path(
            _env("COGNEE_DATA_ROOT", str(PROJECT_ROOT / ".cognee_data"))
        ).resolve(),
        cognee_system_root=Path(
            _env("COGNEE_SYSTEM_ROOT", str(PROJECT_ROOT / ".cognee_system"))
        ).resolve(),
        graph_db_provider=_env("GRAPH_DATABASE_PROVIDER", "kuzu"),
        vector_db_provider=_env("VECTOR_DB_PROVIDER", "lancedb"),
    )
