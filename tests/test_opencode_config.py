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


def _settings(*, profile: str = "poc") -> Settings:
    """Minimum-fields Settings for tests — only the fields build_opencode_config
    actually reads."""
    return Settings(
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key="sk-test",
        extraction_model="gpt-4o",
        reasoning_model="gpt-4o",
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
