"""opencode config builder — pure function for the env-injected opencode config.

opencode reads its config from `OPENCODE_CONFIG_CONTENT` env var (set at
spawn) instead of reading `opencode.json` from the workspace. This is the
load-bearing security boundary: the agent cannot self-modify its own
permission policy, MCP servers, or any other knob the operator controls.

Two profiles, switched via Settings.agent_profile:
  - "poc"  — bash tool enabled (with approval prompt). Trusted developer
             driving their own POC; needs full agent power for fab data
             exploration.
  - "prod" — bash tool denied. Multi-user prod; whitelist-only tooling
             (read/write within workspace + KB MCPs).

Tests cover the OUR-side contract: which keys are present, which values
flip with profile. The actual opencode acceptance of the config schema
is verified later by the integration test that spawns a real
`opencode serve` with this config.
"""

from __future__ import annotations

from rca.config import Settings
from rca.services.opencode_config import build_opencode_config


def _settings(
    *,
    profile: str = "poc",
    opencode_llm_provider: str = "openai",
    opencode_llm_model: str = "gpt-4o",
) -> Settings:
    """Minimum-fields Settings for tests — only the fields build_opencode_config
    actually reads."""
    return Settings(
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key="sk-test",
        extraction_model="gpt-4o",
        reasoning_model="gpt-4o",
        opencode_llm_provider=opencode_llm_provider,
        opencode_llm_model=opencode_llm_model,
        openai_api_key="sk-test",
        anthropic_api_key="",
        cognee_data_root=__import__("pathlib").Path("/tmp/test_cognee_data"),
        cognee_system_root=__import__("pathlib").Path("/tmp/test_cognee_sys"),
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1024,
        embedding_endpoint="http://127.0.0.1:8766/v1",
        embedding_api_key="",
        local_embedding_model_path="",
        embedding_server_host="127.0.0.1",
        embedding_server_port=8766,
        graph_db_provider="kuzu",
        vector_db_provider="lancedb",
        log_level="INFO",
        autocrud_data_root=__import__("pathlib").Path("/tmp/test_autocrud"),
        autocrud_user="poc-admin",
        kb_api_base_url="http://127.0.0.1:8765",
        agent_profile=profile,  # ty: ignore[invalid-argument-type]
    )


# ─── model wiring ──────────────────────────────────────────────────────────


def test_model_rendered_as_provider_slash_model() -> None:
    """opencode addresses LLMs by `<provider>/<model>` (models.dev convention).
    The opencode_llm_provider + opencode_llm_model fields must compose into
    that exact form so opencode picks up the operator's choice instead of
    silently falling back to its own default."""
    cfg = build_opencode_config(_settings())
    assert cfg["model"] == "openai/gpt-4o", (
        f"expected 'openai/gpt-4o', got {cfg['model']!r}"
    )


def test_instructions_points_at_template_agents_md() -> None:
    """AGENTS.md is the orientation file opencode auto-prepends to the agent's
    system prompt. We block opencode's project-level discovery for security
    (OPENCODE_DISABLE_PROJECT_CONFIG=true), so this `instructions` field is
    the controlled re-entry: opencode loads the kb-api-blessed AGENTS.md
    via this absolute-path list. If the path drifts (template moved, but
    config not updated), the agent loses its workspace orientation."""
    cfg = build_opencode_config(_settings())
    assert "instructions" in cfg, "missing `instructions` field"
    assert isinstance(cfg["instructions"], list), "`instructions` must be a list"
    assert any(
        path.endswith("templates/case_workspace/AGENTS.md")
        for path in cfg["instructions"]
    ), (
        f"AGENTS.md path missing from instructions: {cfg['instructions']!r}"
    )


def test_default_agent_is_rca_agent() -> None:
    """opencode's UI opens on `default_agent` if set, else falls back to
    `build`. We seed every workspace with `.opencode/agents/rca-agent.md`
    and want the UI to land on it without manual switching."""
    cfg = build_opencode_config(_settings())
    assert cfg["default_agent"] == "rca-agent", (
        f"expected default_agent='rca-agent', got {cfg.get('default_agent')!r}"
    )


def test_opencode_uses_dedicated_llm_setting_independent_of_kb_api() -> None:
    """The opencode chat agent and kb-api's extraction/reasoning models are
    intentionally separate — operator can pair, e.g., a cheap extraction
    model with a stronger user-facing chat model. build_opencode_config must
    only consult the opencode_* fields, not llm_provider/llm_model."""
    cfg = build_opencode_config(
        _settings(
            opencode_llm_provider="anthropic",
            opencode_llm_model="claude-sonnet-4-5",
        )
    )
    assert cfg["model"] == "anthropic/claude-sonnet-4-5", (
        f"opencode model should track opencode_llm_*, got {cfg['model']!r}"
    )


# ─── load_settings env-var fallback ────────────────────────────────────────


def _base_env(monkeypatch, tmp_path) -> None:
    """Minimum env for load_settings to succeed — provider=openai with key."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("AUTOCRUD_DATA_ROOT", str(tmp_path / "autocrud"))
    monkeypatch.setenv("COGNEE_DATA_ROOT", str(tmp_path / "cognee_data"))
    monkeypatch.setenv("COGNEE_SYSTEM_ROOT", str(tmp_path / "cognee_system"))
    # Wipe potential leakage from the host shell
    monkeypatch.delenv("OPENCODE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENCODE_LLM_MODEL", raising=False)


def test_opencode_llm_falls_back_to_kb_api_settings_when_unset(
    monkeypatch, tmp_path
) -> None:
    """When OPENCODE_LLM_PROVIDER/MODEL are unset, opencode_llm_* should
    inherit from llm_provider/llm_model — operators who don't care about
    the split shouldn't have to configure it."""
    from rca.config import load_settings

    _base_env(monkeypatch, tmp_path)
    s = load_settings()
    assert s.opencode_llm_provider == "openai"
    assert s.opencode_llm_model == "gpt-4o"


def test_opencode_llm_takes_dedicated_env_vars_when_set(
    monkeypatch, tmp_path
) -> None:
    """OPENCODE_LLM_PROVIDER/MODEL override the kb-api defaults."""
    from rca.config import load_settings

    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENCODE_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("OPENCODE_LLM_MODEL", "claude-haiku-4-5")
    s = load_settings()
    assert s.opencode_llm_provider == "anthropic"
    assert s.opencode_llm_model == "claude-haiku-4-5"


def test_switching_opencode_provider_alone_picks_that_providers_default_model(
    monkeypatch, tmp_path
) -> None:
    """If only OPENCODE_LLM_PROVIDER is set (different from LLM_PROVIDER),
    the default model should match the new provider — not blindly carry
    over llm_model, which would point at the wrong provider's catalog."""
    from rca.config import load_settings

    _base_env(monkeypatch, tmp_path)  # LLM_PROVIDER=openai, LLM_MODEL=gpt-4o
    monkeypatch.setenv("OPENCODE_LLM_PROVIDER", "anthropic")
    s = load_settings()
    assert s.opencode_llm_provider == "anthropic"
    assert s.opencode_llm_model != "gpt-4o", (
        "opencode_llm_model should not silently keep an openai model when "
        "opencode_llm_provider was switched to anthropic"
    )


def test_opencode_llm_provider_anthropic_requires_anthropic_key(
    monkeypatch, tmp_path
) -> None:
    """opencode reads ANTHROPIC_API_KEY from the inherited process env. If
    the operator picks the anthropic provider for opencode but didn't set
    the key, fail loudly at config-load time, not silently at first chat."""
    import pytest

    from rca.config import load_settings

    _base_env(monkeypatch, tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENCODE_LLM_PROVIDER", "anthropic")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        load_settings()


def test_api_key_not_embedded_in_config() -> None:
    """The opencode config travels via OPENCODE_CONFIG_CONTENT env var. We
    rely on opencode reading OPENAI_API_KEY / ANTHROPIC_API_KEY from the
    inherited process env, not the config payload, so secrets don't end up
    in logs or process listings that capture env values."""
    import json

    settings = _settings()
    cfg = build_opencode_config(settings)
    serialized = json.dumps(cfg)
    assert settings.openai_api_key not in serialized
    assert settings.llm_api_key not in serialized


# ─── permission profile (security-critical) ────────────────────────────────


def test_poc_profile_allows_bash_with_approval() -> None:
    """POC profile keeps bash available — the developer is driving their own
    machine and needs full agent power for fab-data exploration. Approval
    prompt remains so accidental destructive commands are caught."""
    cfg = build_opencode_config(_settings(profile="poc"))
    assert cfg["permission"]["bash"] != "deny", (
        "POC must allow bash (with approval); only prod profile bans it"
    )


def test_prod_profile_denies_bash() -> None:
    """Prod profile must DENY bash — multi-user prod surface where allowing
    bash would let any agent run arbitrary commands inside the opencode
    process's filesystem view. Whitelist-only tooling instead."""
    cfg = build_opencode_config(_settings(profile="prod"))
    assert cfg["permission"]["bash"] == "deny", (
        "prod profile MUST set bash=deny (security boundary)"
    )


def test_edit_always_asks_for_approval() -> None:
    """File edits (write_file / edit_file) need user approval in BOTH profiles.
    Even POC: agent shouldn't silently rewrite the workspace; user wants to
    see the diff."""
    for profile in ("poc", "prod"):
        cfg = build_opencode_config(_settings(profile=profile))
        assert cfg["permission"]["edit"] == "ask", (
            f"profile={profile}: edit must require approval"
        )


def test_external_directory_denied_for_all_profiles() -> None:
    """The agent must stay confined to the workspace dir. Both profiles set
    `external_directory: deny` so every filesystem tool — read, edit, bash,
    glob, grep, list — refuses paths outside the workspace at the tool
    boundary. (MCP server subprocesses are separate and unaffected.)"""
    for profile in ("poc", "prod"):
        cfg = build_opencode_config(_settings(profile=profile))
        assert cfg["permission"]["external_directory"] == "deny", (
            f"profile={profile}: external_directory must be 'deny' to keep "
            f"the agent inside its workspace"
        )


# ─── MCP server registration ───────────────────────────────────────────────


def test_all_three_rca_mcp_servers_registered() -> None:
    """The agent uses three MCP servers in the 9-step RCA flow:
      - kb-mcp        : retain/recall against the cognee-backed KB
      - wafer-data-mcp: pull wafer history + defect counts
      - stats-algo-mcp: run the spurious-correlation scorer

    All three must appear in the opencode config — agent without them is
    useless."""
    cfg = build_opencode_config(_settings())
    mcp = cfg["mcp"]
    assert "kb-mcp" in mcp, "kb-mcp missing — agent cannot recall KB"
    assert "wafer-data-mcp" in mcp, "wafer-data-mcp missing — no wafer/defect data"
    assert "stats-algo-mcp" in mcp, "stats-algo-mcp missing — no candidate scoring"


def test_kb_mcp_passes_kb_api_base_url_from_settings() -> None:
    """kb-mcp speaks to the KB API via KB_API_BASE_URL env var; the value
    MUST come from Settings (not hardcoded) so prod / staging point at the
    right service."""
    settings = _settings()
    cfg = build_opencode_config(settings)
    kb_mcp = cfg["mcp"]["kb-mcp"]
    assert kb_mcp["env"]["KB_API_BASE_URL"] == settings.kb_api_base_url


def test_mcp_servers_use_local_subprocess_type() -> None:
    """All three RCA MCP servers run as local subprocesses (uv run <name>),
    not remote URLs. Document this explicitly so future migration to
    remote MCP servers (e.g. centralized fab-data service) is a deliberate
    decision, not an accident."""
    cfg = build_opencode_config(_settings())
    for name in ("kb-mcp", "wafer-data-mcp", "stats-algo-mcp"):
        server = cfg["mcp"][name]
        assert server["type"] == "local", (
            f"{name} should be type=local for POC; remote requires separate hosting"
        )
        assert "command" in server, f"{name} missing command"
