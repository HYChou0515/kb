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

import logging
import os
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from agents.mcp import MCPServerStdio

logger = logging.getLogger(__name__)

OnProgress = Callable[
    [str, str, float, float | None, str | None], Coroutine[Any, Any, None]
]
"""Callback signature: (server_name, tool_name, progress, total, message)."""


class _ProgressAwareMCPServer(MCPServerStdio):
    """`MCPServerStdio` that surfaces server-side progress notifications.

    The Agents SDK's stock `call_tool` doesn't thread a `progress_callback`
    through to the underlying `ClientSession`, which means the MCP server's
    `ctx.report_progress(...)` is silently dropped — there's no
    progressToken on the request and no callback registered.

    We can't override that politely (the SDK's retry / serialize plumbing
    is in private methods), so we monkey-patch `session.call_tool` for the
    duration of one `call_tool` invocation: the patched version injects a
    `progress_callback` that forwards to our `on_progress` hook.  Parent
    retry / validation logic still runs untouched.
    """

    def __init__(
        self,
        *args: Any,
        on_progress: OnProgress | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._on_progress = on_progress

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None,
        meta: dict[str, Any] | None = None,
    ) -> Any:
        on_progress = self._on_progress
        session = self.session
        if on_progress is None or session is None:
            return await super().call_tool(tool_name, arguments, meta)

        server_name = self.name or "?"

        async def _cb(
            progress: float, total: float | None, message: str | None
        ) -> None:
            try:
                await on_progress(
                    server_name, tool_name, progress, total, message
                )
            except Exception:  # noqa: BLE001 — never break the call on UI error
                logger.exception("on_progress callback failed")

        orig = session.call_tool

        async def _patched(
            name: str,
            arguments: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> Any:
            kwargs.setdefault("progress_callback", _cb)
            return await orig(name, arguments, **kwargs)

        session.call_tool = _patched  # type: ignore[method-assign]
        try:
            return await super().call_tool(tool_name, arguments, meta)
        finally:
            session.call_tool = orig  # type: ignore[method-assign]


def build_servers(
    *,
    workspace: Path,
    npx_bin: str = "npx",
    tool_timeout: float = 300.0,
    on_progress: OnProgress | None = None,
) -> list[MCPServerStdio]:
    """Build the agent's MCP server list anchored to `workspace`.

    `tool_timeout` is the per-tool-call timeout (seconds) for every
    stdio MCP server we own.  OpenAI Agents SDK's default is 5s, which
    is fine for `read_file` but too short for fab data fetches that
    can run a minute or more — pass a generous value (we default
    callers to 300s via UISettings).

    `on_progress` is an async callback that receives
    `(server_name, tool_name, progress, total, message)` whenever a tool
    emits a progress notification via `ctx.report_progress(...)`.  Useful
    for showing live progress in the chat UI while a tool is running.

    Caller owns the lifecycle: must `await server.connect()` before
    handing to Agent, and `await server.cleanup()` on close.

    Set `RCA_UI_ENABLE_KB_MCP=0` in the env to skip the kb-mcp server —
    useful for local testing when kb-api / cognee isn't running.
    """
    servers: list[MCPServerStdio] = [
        _filesystem_server(workspace, npx_bin, tool_timeout, on_progress),
        _wafer_data_mcp_server(tool_timeout, on_progress),
        _stats_algo_mcp_server(tool_timeout, on_progress),
    ]
    if os.getenv("RCA_UI_ENABLE_KB_MCP", "1") != "0":
        servers.insert(1, _kb_mcp_server(tool_timeout, on_progress))
    return servers


def _filesystem_server(
    workspace: Path,
    npx_bin: str,
    tool_timeout: float,
    on_progress: OnProgress | None,
) -> MCPServerStdio:
    # The official MCP filesystem server takes one or more allowed dirs as
    # positional args. Restricting to a single dir IS our sandbox — any
    # path outside `workspace` is rejected by the server before we even
    # see the request, which replaces opencode's external_directory:deny.
    return _ProgressAwareMCPServer(
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
        client_session_timeout_seconds=tool_timeout,
        on_progress=on_progress,
    )


def _kb_mcp_server(
    tool_timeout: float, on_progress: OnProgress | None
) -> MCPServerStdio:
    return _ProgressAwareMCPServer(
        name="kb-mcp",
        params={
            "command": "uv",
            "args": ["run", "--quiet", "kb-mcp"],
            "env": _inherit_env(),
        },
        cache_tools_list=True,
        client_session_timeout_seconds=tool_timeout,
        on_progress=on_progress,
    )


def _wafer_data_mcp_server(
    tool_timeout: float, on_progress: OnProgress | None
) -> MCPServerStdio:
    return _ProgressAwareMCPServer(
        name="wafer-data-mcp",
        params={
            "command": "uv",
            "args": ["run", "--quiet", "wafer-data-mcp"],
            "env": _inherit_env(),
        },
        cache_tools_list=True,
        client_session_timeout_seconds=tool_timeout,
        on_progress=on_progress,
    )


def _stats_algo_mcp_server(
    tool_timeout: float, on_progress: OnProgress | None
) -> MCPServerStdio:
    return _ProgressAwareMCPServer(
        name="stats-algo-mcp",
        params={
            "command": "uv",
            "args": ["run", "--quiet", "stats-algo-mcp"],
            "env": _inherit_env(),
        },
        cache_tools_list=True,
        client_session_timeout_seconds=tool_timeout,
        on_progress=on_progress,
    )


def _inherit_env() -> dict[str, str]:
    """The MCP servers need our env (PATH, HOME, *_API_KEY, LLM_*,
    COGNEE_DATA_ROOT, etc.). Forward the whole thing — they're our own
    subprocesses, not untrusted code."""
    return dict(os.environ)
