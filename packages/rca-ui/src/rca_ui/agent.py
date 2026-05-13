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

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
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
class TurnDoneEvent:
    """Marks end of turn. Yielded once after history has been persisted."""

    final_output: str


StreamEvent = TextDeltaEvent | ToolCallEvent | ToolOutputEvent | TurnDoneEvent


_RCA_SYSTEM_PROMPT = """\
You are a senior semiconductor process integration engineer running a root-cause
analysis (RCA) session with the user. Drive a structured 9-step interactive
flow, leveraging:

  - wafer-data-mcp — pull wafer process history + per-wafer defect counts
  - stats-algo-mcp — run the in-house statistical scorer (over-generates
                     false alarms by design)
  - kb-mcp         — knowledge graph (cognee). 5 tools:
                       remember(text, dataset_name, …)
                       recall(query, datasets, top_k, session_id)
                       search(query, query_type, datasets, top_k)
                       improve(dataset, …)
                       forget(data_id|dataset|everything)
                     Trust tier is encoded in dataset_name:
                       "rca_reports"      ← highest (manager-signed RCAs)
                       "rca_conversations"← mid (digested RCA chats)
                       "rca_literature"   ← baseline (textbooks/primers)
  - filesystem     — read / write files in the case workspace dir

Your unique value is FILTERING: stats produces many high-scoring factors,
most of which are spurious because of small wafer N and high factor
dimensionality. You drop no-mechanism candidates using the KB and surface
only those with a defensible physical pathway.

# Workspace files (filesystem MCP, absolute paths only)

  - CASE.md           — case metadata (read-only; auto-rendered)
  - notes.md          — your scratchpad, append cumulative observations
  - draft_report.md   — the report you and the user co-author

Always read CASE.md first.

# 9-step flow

1. Get wafer + defect data (ask user OR wafer-data-mcp.list_lots).
2. Characterize defect (defect_type, scan_stage). wafer-data-mcp.get_defect_summary if needed.
3. Suspicious stage range from the user.
4. Suspicious factor type (default: tool assignment).
5. wafer-data-mcp.download_wafer_history with steps 1/3/4 inputs.
6. Drop dummy/scribe steps (confirm with user).
7. stats-algo-mcp.compute_factor_scores. Tell user: "These include false
   alarms; we'll filter them with the KB."
8. ★ For each top-K candidate:
     - Formulate as a query.
     - kb-mcp.recall(query=…, datasets=["rca_reports", "rca_literature"]).
       The answer is plain text; YOU extract verdict (plausible / uncertain
       / implausible) + cite the sources cognee returns.
     - Pause and ask 「以上是 KB 過濾後的結果。哪些 verdict 跟你直覺不合?」
     - F1-F4 grilling on user reactions; capture conditions/magnitude/mechanism.
9. Co-author the final RCA report (zh-TW; technical terms in English):
   defect_summary / root_cause / ruled_out / confounders / actions /
   kb_gaps / kb_feedback / glossary.
   Iterate; only save when user says "agreed / 同意 / OK 存吧". Then:
     a. Save to <workspace>/reports/RCA-<case_id>-<YYYYMMDD>.md.
     b. kb-mcp.remember(text=<full report>, dataset_name="rca_reports",
                        self_improvement=True).
     c. kb-mcp.remember(text=<transcript summary>,
                        dataset_name="rca_conversations").
   Confirm both to the user.

# Behavior rules

  - Never fabricate a mechanism. Empty / implausible recall → drop or flag.
  - Always cite KB sources when presenting a mechanism.
  - Distinguish "the KB said X" from "I think X".
  - Ask, don't assume. Defaults are explicit; always confirm.
  - Stay terse.
  - Conversation language: 繁體中文 (Taiwan). Keep technical terms,
    acronyms, tool/step IDs, materials in their original English.
  - The RCA report is the canonical learning artifact. F1-F4 feedback
    must reach Section 7. Never skip the dual-save (9b + 9c).
"""


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
    ) -> None:
        self._workspace_root = workspace_root
        self._model = model
        self._npx_bin = npx_bin
        self._mcp_servers = build_servers(workspace=workspace_root, npx_bin=npx_bin)
        self._agent: Agent | None = None
        self._case_id: str | None = None
        self._workspace: Path | None = None
        self._history: list = []  # list[TResponseInputItem]
        self._started = False

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
        Agent object with a fresh system prompt; MCP servers stay put."""
        self._case_id = case_id
        self._workspace = workspace
        self._history = []
        ws_abs = str(workspace.resolve())
        kb_enabled = any(s.name == "kb-mcp" for s in self._mcp_servers)
        kb_note = (
            ""
            if kb_enabled
            else (
                "\nKB MODE: kb-mcp is DISABLED for this session. "
                "Skip step 8 (KB recall filtering); after step 7 stats, "
                "present the raw candidate list to the user with the caveat "
                "that false alarms are not filtered. Skip step 9b/9c "
                "(kb-mcp.remember dual-save) — save only the local report file.\n"
            )
        )
        self._agent = Agent(
            name="rca-agent",
            instructions=(
                _RCA_SYSTEM_PROMPT
                + "\n\n# This session\n"
                f"\nCase ID: {case_id}\n"
                f"\nFilesystem MCP is sandboxed to: {self._workspace_root}\n"
                f"Your case workspace is: {ws_abs}\n"
                + kb_note
                + "\nALWAYS pass absolute paths to filesystem tools.\n"
                "Examples for this session:\n"
                f"  read_file path={ws_abs}/CASE.md\n"
                f"  write_file path={ws_abs}/notes.md\n"
                f"  edit_file path={ws_abs}/draft_report.md\n"
                "Never use bare filenames or paths starting with `./` —\n"
                "the filesystem MCP rejects them with 'not in allowed directories'.\n"
            ),
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
          ToolOutputEvent   — tool returned (name, stringified output)
          TurnDoneEvent     — final, exactly once; history is persisted by then

        Conversation memory is held in `self._history`; the entire list is
        passed in each call, and `result.to_input_list()` rebuilds it at
        end-of-turn so the agent retains tool-call context across turns.
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

        async for raw in result.stream_events():
            if raw.type == "raw_response_event":
                data = raw.data
                if getattr(data, "type", "") == "response.output_text.delta":
                    delta = getattr(data, "delta", "") or ""
                    if delta:
                        yield TextDeltaEvent(delta=delta)
                continue

            if raw.type == "run_item_stream_event":
                if raw.name == "tool_called":
                    name, args, call_id = _extract_tool_call(raw.item.raw_item)
                    if call_id:
                        call_names[call_id] = name
                    yield ToolCallEvent(name=name, arguments=args)
                elif raw.name == "tool_output":
                    call_id = _extract_call_id(raw.item.raw_item)
                    name = call_names.get(call_id or "", "")
                    yield ToolOutputEvent(
                        name=name, output=_stringify(raw.item.output)
                    )

        self._history = result.to_input_list()
        yield TurnDoneEvent(final_output=result.final_output or "")

    def load_history(self, history: list) -> None:
        """Resume support: rehydrate `self._history` from a prior transcript.
        Caller is responsible for shaping the list as TResponseInputItem
        records (role / content)."""
        self._history = list(history)


# ─── helpers ──────────────────────────────────────────────────────────────


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
