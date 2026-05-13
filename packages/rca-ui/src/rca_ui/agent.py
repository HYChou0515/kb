"""OpenAI Agents SDK wiring for the RCA agent.

In-process replacement for opencode's `rca-agent`. Tools come from four
MCP stdio subprocesses (filesystem / kb-mcp / wafer-data-mcp /
stats-algo-mcp) we own.

Lifecycle:
    rt = AgentRuntime(workspace_root=..., model=...)
    await rt.start()                       # spawn MCPs once
    rt.bind_case(case_id=..., workspace=...)  # rebind per case (cheap)
    out = await rt.run_user_turn("hello")
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any

from agents import Agent, RunConfig, Runner

from rca_ui.mcp_setup import build_servers

logger = logging.getLogger(__name__)


# ─── streaming event surface ──────────────────────────────────────────────


@dataclass
class TextDeltaEvent:
    """An incremental chunk of assistant text."""

    delta: str


@dataclass
class ToolCallEvent:
    """The model requested a tool. `arguments` is the raw JSON string."""

    name: str
    arguments: str


@dataclass
class ToolOutputEvent:
    """The tool returned. `output` is stringified for display."""

    name: str
    output: str


@dataclass
class ReasoningDeltaEvent:
    """A chunk of model reasoning ("think") output, separate from the
    user-visible answer.  Surfaced by Qwen / DeepSeek-R1 / o1-class models
    via the `reasoning_content` field on chat-completion deltas; the
    Agents SDK normalises these into `response.reasoning_text.delta` and
    `response.reasoning_summary_text.delta` raw events."""

    delta: str


@dataclass
class ProgressEvent:
    """A progress update from an in-flight MCP tool. Tools opt in by
    calling `ctx.report_progress(progress, total, message)` server-side.
    UI can update the latest tool chip in place rather than wait for the
    final ToolOutputEvent — useful when a fab data fetch takes minutes."""

    tool_name: str
    progress: float
    total: float | None
    message: str


@dataclass
class TurnDoneEvent:
    """Marks end of turn. Yielded once after history has been persisted."""

    final_output: str


StreamEvent = (
    TextDeltaEvent
    | ReasoningDeltaEvent
    | ToolCallEvent
    | ToolOutputEvent
    | ProgressEvent
    | TurnDoneEvent
)


# ─── prompt loading ──────────────────────────────────────────────────────
#
# All instructions live under `prompts/` next to this module so they're
# easy to audit / diff in one place.  Edits require a server restart —
# loaded once at import.

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _read_prompt(name: str) -> str:
    path = _PROMPTS_DIR / name
    if not path.exists():
        raise RuntimeError(
            f"prompt file missing: {path} — check rca_ui/prompts/README.md"
        )
    return path.read_text(encoding="utf-8")


_SYSTEM_PROMPT = _read_prompt("system.md")
_SESSION_TEMPLATE = Template(_read_prompt("session.md.tpl"))
_KB_DISABLED_NOTE = _read_prompt("kb_disabled.md")


class AgentRuntime:
    """Process-level singleton. Spawns MCP servers ONCE at startup and
    reuses them across cases.

    Why singleton: OAI Agents SDK's MCPServerStdio uses anyio task groups
    bound to the task that called connect(). Tearing them down from
    another task (or letting GC try to do it) raises "cancel scope in
    different task" errors that corrupt the event loop. Keeping a single
    long-lived runtime sidesteps the whole issue — the MCPs live until
    the rca-ui process exits.

    The filesystem MCP is rooted at `workspace_root` (the parent of all
    case dirs) so a case switch needs no MCP restart — the agent system
    prompt is rebuilt per case, but the tool surface stays put.
    """

    def __init__(
        self,
        *,
        workspace_root: Path,
        model: str,
        npx_bin: str = "npx",
        mcp_tool_timeout: float = 300.0,
    ) -> None:
        self._workspace_root = workspace_root
        self._model = model
        self._npx_bin = npx_bin
        # Bound here so build_servers can pass it down to each MCPServerStdio.
        # Fires for every progress notification the MCP servers send while a
        # turn is in flight; the active run_user_turn_streamed coroutine
        # consumes it via self._progress_queue.
        self._mcp_servers = build_servers(
            workspace=workspace_root,
            npx_bin=npx_bin,
            tool_timeout=mcp_tool_timeout,
            on_progress=self._on_mcp_progress,
        )
        self._agent: Agent | None = None
        self._case_id: str | None = None
        self._workspace: Path | None = None
        self._history: list = []  # list[TResponseInputItem]
        self._started = False
        # Set for the duration of one run_user_turn_streamed turn; None
        # otherwise.  Progress notifications outside a turn are dropped.
        self._progress_queue: "asyncio.Queue[StreamEvent | object] | None" = None

    async def _on_mcp_progress(
        self,
        server_name: str,
        tool_name: str,
        progress: float,
        total: float | None,
        message: str | None,
    ) -> None:
        """Called by every MCPServerStdio whenever a `notifications/progress`
        arrives mid-tool-call.  We forward it into the current turn's
        event queue so the UI sees it interleaved with other stream events."""
        q = self._progress_queue
        if q is None:
            return
        await q.put(
            ProgressEvent(
                tool_name=tool_name,
                progress=progress,
                total=total,
                message=message or "",
            )
        )

    async def start(self) -> None:
        if self._started:
            return
        for s in self._mcp_servers:
            await s.connect()
        self._started = True

    @property
    def case_id(self) -> str | None:
        """Currently-bound case, or None before the first bind_case()."""
        return self._case_id

    def bind_case(self, *, case_id: str, workspace: Path) -> None:
        """Re-anchor the agent to a new case. Cheap — just rebuilds the
        Agent object with a fresh system prompt; MCP servers stay put.

        Instructions are composed from `prompts/system.md` and
        `prompts/session.md.tpl` (see `prompts/README.md`)."""
        self._case_id = case_id
        self._workspace = workspace
        self._history = []
        ws_abs = str(workspace.resolve())
        kb_enabled = any(s.name == "kb-mcp" for s in self._mcp_servers)
        session_block = _SESSION_TEMPLATE.substitute(
            case_id=case_id,
            workspace_root=str(self._workspace_root),
            ws_abs=ws_abs,
            kb_note="" if kb_enabled else _KB_DISABLED_NOTE,
        )
        self._agent = Agent(
            name="rca-agent",
            instructions=_SYSTEM_PROMPT + "\n" + session_block,
            mcp_servers=self._mcp_servers,
            model=self._model,
        )

    async def stop(self) -> None:
        # No-op. Process-level singleton — see class docstring. MCP children
        # die when rca-ui exits (OS reaps them).
        return

    async def run_user_turn_streamed(
        self, user_input: str
    ) -> AsyncIterator[StreamEvent]:
        """Run one turn with streaming. Yields:

          TextDeltaEvent    — each assistant text chunk
          ToolCallEvent     — model invoked a tool (name, arguments JSON)
          ProgressEvent    — MCP tool reported `ctx.report_progress(...)`
          ToolOutputEvent   — tool returned (name, stringified output)
          TurnDoneEvent     — final, exactly once; history is persisted by then

        Conversation memory is held in `self._history`; the entire list is
        passed in each call, and `result.to_input_list()` rebuilds it at
        end-of-turn so the agent retains tool-call context across turns.

        SDK events and out-of-band MCP progress notifications are merged
        through one asyncio.Queue: a pump task drains result.stream_events
        into the queue, and `_on_mcp_progress` also writes to it, so the
        consumer sees them in arrival order.
        """
        if self._agent is None:
            raise RuntimeError("AgentRuntime.start() not called")
        new_input = self._history + [{"role": "user", "content": user_input}]
        result = Runner.run_streamed(
            starting_agent=self._agent,
            input=new_input,
            max_turns=30,
            run_config=RunConfig(workflow_name=f"rca:{self._case_id}"),
        )

        # Map call_id → tool name so we can label ToolOutputEvent. The
        # tool_output run-item doesn't always echo the name; we read it from
        # the matching tool_called item we saw earlier.
        call_names: dict[str, str] = {}
        queue: asyncio.Queue[StreamEvent | object] = asyncio.Queue()
        DONE = object()  # sentinel pushed when SDK stream is exhausted
        self._progress_queue = queue

        async def pump_sdk() -> None:
            try:
                async for raw in result.stream_events():
                    evt = _translate_sdk_event(raw, call_names)
                    if evt is not None:
                        await queue.put(evt)
            finally:
                await queue.put(DONE)

        pump_task = asyncio.create_task(pump_sdk())
        try:
            while True:
                item = await queue.get()
                if item is DONE:
                    break
                yield item  # type: ignore[misc]
        finally:
            self._progress_queue = None
            if not pump_task.done():
                pump_task.cancel()
                try:
                    await pump_task
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass

        self._history = result.to_input_list()
        yield TurnDoneEvent(final_output=result.final_output or "")

    def load_history(self, history: list) -> None:
        """Resume support: rehydrate `self._history` from a prior transcript.
        Caller is responsible for shaping the list as TResponseInputItem
        records (role / content)."""
        self._history = list(history)


# ─── helpers ──────────────────────────────────────────────────────────────


# Raw event `.type` values we surface as deltas.  Both OpenAI's native
# Responses API and the Agents SDK's chat-completions → Responses
# adapter (used for LiteLLM / Qwen / DeepSeek / etc.) emit these.
_TEXT_DELTA_TYPES = frozenset({"response.output_text.delta"})
_REASONING_DELTA_TYPES = frozenset(
    {
        # Adapter for chat-completions models that expose `reasoning_content`
        # on the delta (Qwen 3, DeepSeek-R1, o1-class via LiteLLM, …).
        "response.reasoning_text.delta",
        "response.reasoning_summary_text.delta",
    }
)


def _translate_sdk_event(
    raw: Any, call_names: dict[str, str]
) -> StreamEvent | None:
    """Map one raw openai-agents stream event to our flat StreamEvent
    types.  Returns None for events we don't surface.

    Covers both OpenAI Responses API events and the LiteLLM /
    chat-completions adapter's normalised equivalents — they share
    `response.*` event names but a LiteLLM-backed Qwen model also emits
    `response.reasoning_text.delta` for `<think>` tokens, which the
    native OpenAI path never produces.
    """
    if raw.type == "raw_response_event":
        data = raw.data
        et = getattr(data, "type", "")
        if et in _TEXT_DELTA_TYPES:
            delta = getattr(data, "delta", "") or ""
            if delta:
                return TextDeltaEvent(delta=delta)
            return None
        if et in _REASONING_DELTA_TYPES:
            delta = getattr(data, "delta", "") or ""
            if delta:
                return ReasoningDeltaEvent(delta=delta)
            return None
        return None
    if raw.type == "run_item_stream_event":
        if raw.name == "tool_called":
            name, args, call_id = _extract_tool_call(raw.item.raw_item)
            if call_id:
                call_names[call_id] = name
            return ToolCallEvent(name=name, arguments=args)
        if raw.name == "tool_output":
            call_id = _extract_call_id(raw.item.raw_item)
            name = call_names.get(call_id or "", "")
            return ToolOutputEvent(name=name, output=_stringify(raw.item.output))
        if raw.name == "reasoning_item_created":
            # Fallback for paths that emit a single finished item rather
            # than streaming deltas — surface the assembled text in one
            # ReasoningDeltaEvent so the bubble still gets filled.
            text = _extract_reasoning_text(raw.item.raw_item)
            if text:
                return ReasoningDeltaEvent(delta=text)
            return None
    return None


def _extract_reasoning_text(raw_item: Any) -> str:
    """Best-effort extract reasoning text from a ResponseReasoningItem-like
    object.  Different SDK versions / adapters shape this slightly
    differently; we probe a few shapes."""
    if raw_item is None:
        return ""
    # ResponseReasoningItem: .summary is list of {text}; .content is list of {text}
    parts: list[str] = []
    for attr in ("summary", "content"):
        seq = _attr(raw_item, attr, None)
        if not seq:
            continue
        for entry in seq:
            text = _attr(entry, "text", None)
            if text:
                parts.append(str(text))
    if parts:
        return "\n".join(parts)
    # Some adapters stash it directly on `.text`
    text = _attr(raw_item, "text", None)
    return str(text) if text else ""


def _extract_tool_call(raw_item: Any) -> tuple[str, str, str | None]:
    """Pull (name, arguments, call_id) out of a tool_call raw item.

    raw_item is one of ResponseFunctionToolCall / McpCall / dict / etc.
    We probe both attribute and mapping access since the union is wide.
    """
    name = _attr(raw_item, "name", "") or "?"
    args = _attr(raw_item, "arguments", "") or ""
    call_id = _attr(raw_item, "call_id", None) or _attr(raw_item, "id", None)
    return str(name), str(args), call_id


def _extract_call_id(raw_item: Any) -> str | None:
    return _attr(raw_item, "call_id", None) or _attr(raw_item, "id", None)


def _attr(obj: Any, name: str, default: Any) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _stringify(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(x)


# ─── orphan-MCP backstop ───────────────────────────────────────────────────

_MCP_PROCESS_PATTERNS = (
    "kb-mcp",
    "wafer-data-mcp",
    "stats-algo-mcp",
    "@modelcontextprotocol/server-filesystem",
)


def _kill_orphan_mcp_subprocesses() -> None:
    """SIGTERM any MCP subprocess whose parent matches our PID. Backstop
    for the anyio cancel-scope bug where MCPServerStdio.cleanup raises
    before stopping the child. Best-effort — never raises."""
    import os
    import signal
    import subprocess

    try:
        out = subprocess.run(
            ["pgrep", "-P", str(os.getpid())],
            capture_output=True,
            text=True,
            check=False,
        )
        for pid_str in (out.stdout or "").split():
            try:
                pid = int(pid_str)
            except ValueError:
                continue
            cmdline = _read_cmdline(pid)
            if any(p in cmdline for p in _MCP_PROCESS_PATTERNS):
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
    except Exception:  # noqa: BLE001
        logger.debug("orphan kill scan failed", exc_info=True)


def _read_cmdline(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().decode("utf-8", "replace").replace("\x00", " ")
    except OSError:
        return ""
