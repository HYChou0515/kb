"""Configuration loaded from environment variables.

Imported once at process start; rest of the codebase reads from `Settings`
via the dependency-injector Container.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val or ""


_DEFAULT_MODEL_BY_PROVIDER = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-5",
}


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_model: str
    llm_api_key: str

    extraction_model: str
    reasoning_model: str

    openai_api_key: str
    anthropic_api_key: str

    cognee_data_root: Path
    cognee_system_root: Path

    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    embedding_endpoint: str
    embedding_api_key: str
    local_embedding_model_path: str
    embedding_server_host: str
    embedding_server_port: int

    graph_db_provider: str
    vector_db_provider: str

    log_level: str

    autocrud_data_root: Path
    autocrud_user: str

    kb_api_host: str = "127.0.0.1"
    kb_api_port: int = 8765
    kb_api_base_url: str = "http://127.0.0.1:8765"
    mock_fab_data_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "mock-fab-data"
    )

    sources_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "sources")
    benchmark_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "benchmark"
    )

    # Workspace + opencode lifecycle
    idle_threshold_minutes: int = 30
    stale_threshold_days: int = 7
    run_inprocess_watchdog: bool = True
    agent_profile: Literal["poc", "prod"] = "poc"
    opencode_url: str = "http://127.0.0.1:4096"
    opencode_server_password: str = ""
    sweep_secret: str = ""

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
    default_model = _DEFAULT_MODEL_BY_PROVIDER[provider]
    llm_model = _env("LLM_MODEL", default_model)
    extraction_model = _env("EXTRACTION_MODEL", "") or llm_model
    reasoning_model = _env("REASONING_MODEL", "") or llm_model

    return Settings(
        llm_provider=provider,
        llm_model=llm_model,
        llm_api_key=_env("LLM_API_KEY", active_key),
        extraction_model=extraction_model,
        reasoning_model=reasoning_model,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        cognee_data_root=Path(
            _env("COGNEE_DATA_ROOT", str(PROJECT_ROOT / ".cognee_data"))
        ).resolve(),
        cognee_system_root=Path(
            _env("COGNEE_SYSTEM_ROOT", str(PROJECT_ROOT / ".cognee_system"))
        ).resolve(),
        embedding_provider=_env("EMBEDDING_PROVIDER", "openai_compatible"),
        embedding_model=_env("EMBEDDING_MODEL", "local-st"),
        embedding_dimensions=int(_env("EMBEDDING_DIMENSIONS", "1024")),
        embedding_endpoint=_env("EMBEDDING_ENDPOINT", "http://127.0.0.1:8766/v1"),
        embedding_api_key=_env("EMBEDDING_API_KEY", "no-key-required"),
        local_embedding_model_path=_env("LOCAL_EMBEDDING_MODEL_PATH", ""),
        embedding_server_host=_env("EMBEDDING_SERVER_HOST", "127.0.0.1"),
        embedding_server_port=int(_env("EMBEDDING_SERVER_PORT", "8766")),
        graph_db_provider=_env("GRAPH_DATABASE_PROVIDER", "kuzu"),
        vector_db_provider=_env("VECTOR_DB_PROVIDER", "lancedb"),
        log_level=_env("LOG_LEVEL", "INFO"),
        autocrud_data_root=Path(
            _env("AUTOCRUD_DATA_ROOT", "./data/autocrud")
        ).resolve(),
        autocrud_user=_env("AUTOCRUD_USER", "poc-admin"),
        kb_api_host=_env("KB_API_HOST", "127.0.0.1"),
        kb_api_port=int(_env("KB_API_PORT", "8765")),
        kb_api_base_url=_env("KB_API_BASE_URL", "http://127.0.0.1:8765"),
        mock_fab_data_dir=Path(
            _env("MOCK_FAB_DATA_DIR", str(PROJECT_ROOT / "data" / "mock-fab-data"))
        ).resolve(),
        idle_threshold_minutes=int(_env("IDLE_THRESHOLD_MINUTES", "30")),
        stale_threshold_days=int(_env("STALE_THRESHOLD_DAYS", "7")),
        run_inprocess_watchdog=_env("RUN_INPROCESS_WATCHDOG", "true").lower()
        in {"1", "true", "yes"},
        agent_profile=_agent_profile(_env("RCA_AGENT_PROFILE", "poc")),
        opencode_url=_env("OPENCODE_URL", "http://127.0.0.1:4096"),
        opencode_server_password=_env("OPENCODE_SERVER_PASSWORD", ""),
        sweep_secret=_env("SWEEP_SECRET", ""),
    )


def _agent_profile(raw: str) -> Literal["poc", "prod"]:
    """Validate RCA_AGENT_PROFILE — only "poc" or "prod" allowed (controls
    bash tool policy via opencode permissions)."""
    if raw == "poc":
        return "poc"
    if raw == "prod":
        return "prod"
    raise RuntimeError(f"RCA_AGENT_PROFILE must be 'poc' or 'prod', got {raw!r}")
