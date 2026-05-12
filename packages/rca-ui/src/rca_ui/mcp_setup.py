"""MCP server wiring for the rca_ui agent.

Spawns four stdio-based MCP servers and hands them to the OAI Agents SDK
runtime as the agent's tool surface:

    - server-filesystem (npx, opensource)  — workspace-scoped file IO
    - kb-mcp           (in-repo)            — knowledge graph retain / recall
    - wafer-data-mcp   (in-repo)            — fab data loaders
    - stats-algo-mcp   (in-repo)            — statistical scoring

The filesystem server is the only one whose argv changes per session
(allowed-dir = workspace path); the other three are static, so we rebuild
the filesystem entry on each open and reuse the rest.
"""

from __future__ import annotations

import os
from pathlib import Path

from agents.mcp import MCPServerStdio


def build_servers(*, workspace: Path, npx_bin: str = "npx") -> list[MCPServerStdio]:
    """Build the agent's MCP server list anchored to `workspace`.

    Caller owns the lifecycle: must `await server.connect()` before
    handing to Agent, and `await server.cleanup()` on close.

    Set `RCA_UI_ENABLE_KB_MCP=0` in the env to skip the kb-mcp server —
    useful for local testing when kb-api / cognee isn't running.
    """
    servers: list[MCPServerStdio] = [
        _filesystem_server(workspace, npx_bin),
        _wafer_data_mcp_server(),
        _stats_algo_mcp_server(),
    ]
    if os.getenv("RCA_UI_ENABLE_KB_MCP", "1") != "0":
        servers.insert(1, _kb_mcp_server())
    return servers


def _filesystem_server(workspace: Path, npx_bin: str) -> MCPServerStdio:
    # The official MCP filesystem server takes one or more allowed dirs as
    # positional args. Restricting to a single dir IS our sandbox — any
    # path outside `workspace` is rejected by the server before we even
    # see the request, which replaces opencode's external_directory:deny.
    return MCPServerStdio(
        name="filesystem",
        params={
            "command": npx_bin,
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(workspace.resolve()),
            ],
        },
        cache_tools_list=True,
    )


def _kb_mcp_server() -> MCPServerStdio:
    return MCPServerStdio(
        name="kb-mcp",
        params={
            "command": "uv",
            "args": ["run", "--quiet", "kb-mcp"],
            "env": _inherit_env(),
        },
        cache_tools_list=True,
    )


def _wafer_data_mcp_server() -> MCPServerStdio:
    return MCPServerStdio(
        name="wafer-data-mcp",
        params={
            "command": "uv",
            "args": ["run", "--quiet", "wafer-data-mcp"],
            "env": _inherit_env(),
        },
        cache_tools_list=True,
    )


def _stats_algo_mcp_server() -> MCPServerStdio:
    return MCPServerStdio(
        name="stats-algo-mcp",
        params={
            "command": "uv",
            "args": ["run", "--quiet", "stats-algo-mcp"],
            "env": _inherit_env(),
        },
        cache_tools_list=True,
    )


def _inherit_env() -> dict[str, str]:
    """The MCP servers need our env (PATH, HOME, *_API_KEY, LLM_*,
    COGNEE_DATA_ROOT, etc.). Forward the whole thing — they're our own
    subprocesses, not untrusted code."""
    return dict(os.environ)
