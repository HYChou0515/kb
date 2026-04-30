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

from typing import Any

from rca.config import Settings


def build_opencode_config(settings: Settings) -> dict[str, Any]:
    """Render the opencode config dict from Settings + active agent_profile.

    Pure function — no I/O. Result is JSON-serializable and meant to be
    set as the OPENCODE_CONFIG_CONTENT env var when spawning opencode."""
    return {
        "mcp": _mcp_servers(settings),
        "permission": _permission_policy(settings.agent_profile),
    }


def _permission_policy(profile: str) -> dict[str, str]:
    """Per-tool permission policy. "ask" = user approval prompt; "deny" = blocked.
    bash flips between profiles; edit always requires approval."""
    bash_policy = "deny" if profile == "prod" else "ask"
    return {
        "edit": "ask",
        "bash": bash_policy,
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
