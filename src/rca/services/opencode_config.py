"""Build the opencode config dict that gets injected at spawn time.

opencode reads its config from the `OPENCODE_CONFIG_CONTENT` env var
(JSON-encoded) when `OPENCODE_DISABLE_PROJECT_CONFIG=true` is also set —
this is how we keep the agent from self-modifying its own constraints
(it can't reach a config file because there isn't one).

Two profiles control the bash policy (the most security-sensitive knob):

  - "poc"  — bash is "ask" (user approves each command). Trusted single-
             developer machine; agent needs full power for fab-data
             exploration.
  - "prod" — bash is "deny". Multi-user surface where allowing bash would
             let any caller execute arbitrary commands within the
             opencode process's filesystem view. Whitelist-only tooling
             instead.

Edits (write_file / edit_file) always require approval — even POC.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rca.config import Settings

# Absolute path to the kb-api-blessed AGENTS.md (orientation prepended to the
# agent's system prompt). Lives next to the OPENCODE_CONFIG_DIR contents so
# the same dir holds every config artifact opencode loads from outside the
# workspace. We pass it via the `instructions` config field because
# OPENCODE_DISABLE_PROJECT_CONFIG=true blocks opencode's own AGENTS.md
# discovery from the workspace tree (see local_subprocess.py).
#
# __file__ = <project>/src/rca/services/opencode_config.py — climb 4 levels
# (services → rca → src → <project>) to reach the project root.
_AGENTS_MD_PATH = (
    Path(__file__).resolve().parents[3]
    / "templates"
    / "case_workspace"
    / "AGENTS.md"
)


def build_opencode_config(settings: Settings) -> dict[str, Any]:
    """Render the opencode config dict from Settings + active agent_profile.

    Pure function — no I/O. Result is JSON-serializable and meant to be
    set as the OPENCODE_CONFIG_CONTENT env var when spawning opencode.

    `model` is rendered as `<provider>/<model>` because that's opencode's
    models.dev identifier convention. The provider's API key is read by
    opencode from the standard env var (OPENAI_API_KEY / ANTHROPIC_API_KEY)
    inherited from the kb-api process — we don't put the secret in config
    text that ends up in OPENCODE_CONFIG_CONTENT.

    The opencode chat agent's LLM is independent from kb-api's
    extraction/reasoning models (it reads `opencode_llm_provider` /
    `opencode_llm_model` so operators can pair a small backend model with
    a stronger user-facing chat model).

    `default_agent: "rca-agent"` matches the named agent loaded from
    OPENCODE_CONFIG_DIR (templates/case_workspace/.opencode/agents/
    rca-agent.md). Without this the UI opens on opencode's built-in
    `build` agent and the user has to switch manually.

    `instructions: [<AGENTS.md path>]` re-injects the AGENTS.md orientation
    that opencode's project-config discovery would normally pick up. We
    block that discovery (OPENCODE_DISABLE_PROJECT_CONFIG=true) so the
    agent can't smuggle a malicious AGENTS.md via a workspace write — this
    field is the controlled re-entry point for the file we control.
    """
    return {
        "model": f"{settings.opencode_llm_provider}/{settings.opencode_llm_model}",
        "default_agent": "rca-agent",
        "instructions": [str(_AGENTS_MD_PATH)],
        "mcp": _mcp_servers(settings),
        "permission": _permission_policy(settings.agent_profile),
    }


def _permission_policy(profile: str) -> dict[str, str]:
    """Per-tool permission policy. "ask" = user approval prompt; "deny" = blocked.

    bash flips between profiles; edit always requires approval.

    `external_directory: deny` confines every filesystem-touching tool
    (read / edit / bash / glob / grep / list) to within the agent's
    workspace dir. Workspace-relative case files stay reachable;
    `cat /etc/passwd` or `ls ../..` get blocked at the tool boundary.
    See opencode's external-directory.ts for the universal check.

    MCP servers run in their own subprocesses and aren't subject to this
    rule, so wafer-data-mcp / stats-algo-mcp can still serve absolute
    paths to mock fab data outside the workspace.
    """
    bash_policy = "deny" if profile == "prod" else "ask"
    return {
        "edit": "ask",
        "bash": bash_policy,
        "external_directory": "deny",
    }


def _mcp_servers(settings: Settings) -> dict[str, dict[str, Any]]:
    """Three local-subprocess MCP servers the agent uses for the 9-step RCA flow.
    All `command` arrays start with `uv run` so they pick up the project
    venv (the same one the API server runs in)."""
    return {
        "kb-mcp": {
            "type": "local",
            "command": ["uv", "run", "kb-mcp"],
            "env": {
                "KB_API_BASE_URL": settings.kb_api_base_url,
                "LOG_LEVEL": settings.log_level,
            },
        },
        "wafer-data-mcp": {
            "type": "local",
            "command": ["uv", "run", "wafer-data-mcp"],
            "env": {
                "MOCK_FAB_DATA_DIR": str(settings.mock_fab_data_dir),
                "LOG_LEVEL": settings.log_level,
            },
        },
        "stats-algo-mcp": {
            "type": "local",
            "command": ["uv", "run", "stats-algo-mcp"],
            "env": {
                "MOCK_FAB_DATA_DIR": str(settings.mock_fab_data_dir),
                "LOG_LEVEL": settings.log_level,
            },
        },
    }
