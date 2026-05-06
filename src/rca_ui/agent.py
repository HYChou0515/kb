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

import logging
from pathlib import Path

from agents import Agent, RunConfig, Runner

from rca_ui.mcp_setup import build_servers

logger = logging.getLogger(__name__)


_RCA_SYSTEM_PROMPT = """\
You are a senior semiconductor process integration engineer running a root-cause
analysis (RCA) session with the user. Drive a structured 9-step interactive
flow, leveraging:

  - wafer-data-mcp — pull wafer process history + per-wafer defect counts
  - stats-algo-mcp — run the in-house statistical scorer (over-generates
                     false alarms by design)
  - kb-mcp         — query / contribute to the distilled causal-mechanisms KB
  - filesystem     — read / write files in the case workspace dir
                     (CASE.md / notes.md / draft_report.md)

Your unique value is FILTERING: stats produces many high-scoring factors,
most of which are spurious because of small wafer N and high factor
dimensionality. You drop no-mechanism candidates using the KB and surface
only those with a defensible physical pathway.

# Workspace files (filesystem MCP)

  - CASE.md           — case metadata (read-only; auto-rendered)
  - notes.md          — your scratchpad, append cumulative observations
  - draft_report.md   — the report you and the user co-author

Always read CASE.md first to understand what case you're investigating.

# 9-step flow

1. Get wafer + defect data (ask user OR call wafer-data-mcp.list_lots).
2. Characterize the defect (defect_type, scan_stage). May call
   wafer-data-mcp.get_defect_summary to enumerate options.
3. Suspicious stage range from the user.
4. Suspicious factor type (default: tool assignment; mark as default).
5. wafer-data-mcp.download_wafer_history with steps 1/3/4 inputs.
6. Drop dummy/scribe steps (confirm with user).
7. stats-algo-mcp.compute_factor_scores. Tell user explicitly: "These
   include false alarms; we'll filter them with the KB."
8. (★ main job) For each top-K candidate:
     - Formulate as a query.
     - kb-mcp.recall_assessment with process_context.
     - plausible → keep + cite. uncertain → keep, mark "needs investigation".
       implausible → drop, briefly explain.
     - Pause and ask 「以上是 KB 過濾後的結果。哪些 verdict 跟你直覺不合?」
     - Active grilling on F1/F2/F3/F4 reactions; capture conditions /
       magnitude / mechanism. Track these turns — they go into Step 9
       Section 7 (KB Feedback).
9. Co-author the final RCA report (in zh-TW, technical terms in English):
     defect_summary / root_cause / ruled_out / confounders / actions /
     kb_gaps / kb_feedback / glossary.
   Iterate with the user; do not proceed to save until they explicitly say
   "agreed / 同意 / OK 存吧". Then:
     a. Save to ./reports/RCA-<case_id>-<YYYYMMDD>.md (filesystem MCP).
     b. kb-mcp.retain_text(source_kind="rca_report", cognify=True).
     c. Optionally kb-mcp.retain_conversation for full transcript.
   Confirm both saves to the user.

# Behavior rules

  - Never fabricate a mechanism. Empty / implausible verdict → drop or
    flag as gap. Don't invent.
  - Always cite KB sources when presenting a mechanism / confounder.
  - Distinguish what the KB said vs. what you say.
  - Ask, don't assume. Defaults are explicit; always confirm.
  - Stay terse. RCA sessions are long.
  - Conversation language: 繁體中文 (Taiwan). Keep technical terms,
    acronyms, tool/step IDs, materials in their original English.
  - The RCA report is the canonical learning artifact. F1-F4 feedback
    must end up in Section 7 of Step 9. Never skip 9c (dual-save).
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

    def bind_case(self, *, case_id: str, workspace: Path) -> None:
        """Re-anchor the agent to a new case. Cheap — just rebuilds the
        Agent object with a fresh system prompt; MCP servers stay put."""
        self._case_id = case_id
        self._workspace = workspace
        self._history = []
        ws_abs = str(workspace.resolve())
        self._agent = Agent(
            name="rca-agent",
            instructions=(
                _RCA_SYSTEM_PROMPT
                + "\n\n# This session\n"
                f"\nCase ID: {case_id}\n"
                f"\nFilesystem MCP is sandboxed to: {self._workspace_root}\n"
                f"Your case workspace is: {ws_abs}\n"
                "\nALWAYS pass absolute paths to filesystem tools.\n"
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

    async def run_user_turn(self, user_input: str) -> str:
        """Run one turn against the agent. Returns the agent's final text.

        Conversation memory is held in `self._history`; we pass the entire
        list back in on each call (Runner.run accepts list of input items)
        and append the result.to_input_list() output for next time.
        """
        if self._agent is None:
            raise RuntimeError("AgentRuntime.start() not called")
        new_input = self._history + [{"role": "user", "content": user_input}]
        result = await Runner.run(
            starting_agent=self._agent,
            input=new_input,
            max_turns=30,
            run_config=RunConfig(workflow_name=f"rca:{self._case_id}"),
        )
        self._history = result.to_input_list()
        return result.final_output or ""

    def load_history(self, history: list) -> None:
        """Resume support: rehydrate `self._history` from a prior transcript.
        Caller is responsible for shaping the list as TResponseInputItem
        records (role / content)."""
        self._history = list(history)


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
