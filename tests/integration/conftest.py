"""Integration-test fixtures — real cognee, real embedding server, real LLM.

Boundary check: this conftest only loads for tests under tests/integration/.
Each test marked `@pytest.mark.integration` requires:
  - OPENAI_API_KEY in env (or whatever LLM_PROVIDER points at)
  - embedding server reachable on settings.embedding_endpoint
  - tmpdir-rooted cognee data + system dirs (no pollution of dev .cognee_data)

If any precondition fails, the test is **skipped** (not failed) — local devs
without the embedding server running shouldn't be blocked, and CI can decide
its own enforcement at the make-target level.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import httpx
import pytest
from dotenv import load_dotenv

# Load .env once at conftest import — load_settings() also calls this but the
# precondition checks below run BEFORE load_settings(), so without this the
# key check would skip integration tests on machines that have a working .env
# but no shell-level env vars.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _openai_key_present() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) or bool(os.getenv("LLM_API_KEY"))


def _embedding_server_reachable(url: str) -> bool:
    # /v1/models is the OpenAI-compatible health probe — our local
    # embedding-server implements it.
    try:
        r = httpx.get(url.rstrip("/") + "/models", timeout=1.0)
        return r.status_code < 500
    except Exception:
        return False


@pytest.fixture(scope="session")
def integration_settings(tmp_path_factory: pytest.TempPathFactory):
    """Build a Settings with cognee + autocrud roots under a session tmpdir.

    All preconditions checked here so a failure surfaces once at fixture
    setup time, not 8 times across recall tests."""
    if not _openai_key_present():
        pytest.skip("OPENAI_API_KEY not set — integration tests need a real LLM")

    from rca.config import load_settings

    base = tmp_path_factory.mktemp("cognee_e2e")
    # Override env BEFORE load_settings reads it.
    os.environ["COGNEE_DATA_ROOT"] = str(base / "cognee_data")
    os.environ["COGNEE_SYSTEM_ROOT"] = str(base / "cognee_system")
    os.environ["AUTOCRUD_DATA_ROOT"] = str(base / "autocrud")

    settings = load_settings()

    # Only HTTP-based providers need an endpoint probe. fastembed / ollama /
    # in-process providers run within cognee itself.
    if settings.embedding_provider == "openai_compatible":
        if not _embedding_server_reachable(settings.embedding_endpoint):
            pytest.skip(
                f"embedding server not reachable at {settings.embedding_endpoint} — "
                "start it with `uv run embedding-server` first"
            )

    return settings


@pytest.fixture(scope="session")
def container(integration_settings) -> Iterator:
    """Real DI container, settings overridden to point at tmpdir-rooted cognee.

    Session-scoped because re-cognifying the corpus per test would burn
    minutes + tokens for no isolation gain."""
    from dependency_injector import providers

    from rca.container import Container

    c = Container()
    c.settings.override(providers.Object(integration_settings))
    yield c
    c.unwire()


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
