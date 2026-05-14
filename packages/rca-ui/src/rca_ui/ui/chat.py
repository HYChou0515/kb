"""Chat panel rendering for the case page.

Exports:
- `render_bubble(parent, role, content)` — append one finished
  user/assistant message to the chat list.
- `AssistantStream` — incremental renderer for one streamed
  assistant turn (text deltas, reasoning thinking-block, tool-call
  pills, tool-output lines, live progress).

Bubbles use Quasar's `q-chat-message` (sent → right blue, received →
left white).  Markdown rendering goes through `rca_ui.ui.preview`
(mistune) which handles CJK boundaries correctly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from rca_ui.ui.preview import render_md


def render_bubble(parent: Any, role: str, content: str) -> None:
    """User bubbles render as plain text with literal newlines
    preserved (NiceGUI's `text=` path escapes HTML and turns `\\n`
    into `<br>`).  Assistant bubbles run the full mistune markdown
    pipeline so the model can use bold / lists / tables / code
    fences."""
    sent = role == "user"
    name = "You" if sent else "Agent"
    with parent:
        if sent:
            ui.chat_message(text=content, name=name, sent=True)
        else:
            with ui.chat_message(name=name, sent=False):
                ui.html(render_md(content), sanitize=False)


def _truncate(s: str, n: int) -> str:
    s = (s or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


class AssistantStream:
    """Incremental renderer for one streamed assistant turn.

    Appends items into the chat-list flex column in order:
      💭 reasoning expander (open while think-tokens stream)
      🔧 tool-call pill (one per call)
      ↳  tool-output line (one per result, indented)
      [assistant bubble] — appended-to as text deltas arrive

    A tool call closes the current text bubble, so subsequent text
    deltas start a fresh bubble below it.  Order of interleaving is
    preserved.
    """

    _MAX_ARG_LEN = 240
    _MAX_OUT_LEN = 360

    def __init__(
        self, parent: Any, *, on_update: Callable[[], None] | None = None
    ) -> None:
        self._parent = parent
        self._on_update = on_update
        self._text_md: Any = None
        self._text_buf: list[str] = []
        # Reasoning block (`<think>` from Qwen / DeepSeek-R1 / o1-class).
        # Held open as long as reasoning deltas keep arriving; a non-
        # reasoning event (text / tool) closes it so the next reasoning
        # run starts a fresh expander.
        self._reasoning_md: Any = None
        self._reasoning_buf: list[str] = []
        # Last-rendered tool chip — kept around so live ProgressEvents
        # can rewrite its label in place.
        self._current_tool_label: Any = None
        self._current_tool_head: str = ""

    def _close_text_run(self) -> None:
        self._text_md = None
        self._text_buf = []

    def _close_reasoning_run(self) -> None:
        self._reasoning_md = None
        self._reasoning_buf = []

    def add_text_delta(self, delta: str) -> None:
        # First non-reasoning delta closes any open reasoning block so
        # subsequent reasoning would open a new one below the answer.
        self._close_reasoning_run()
        if self._text_md is None:
            with self._parent:
                with ui.chat_message(name="Agent", sent=False):
                    self._text_md = ui.html("", sanitize=False)
            self._text_buf = []
        self._text_buf.append(delta)
        self._text_md.set_content(render_md("".join(self._text_buf)))
        if self._on_update:
            self._on_update()

    def add_reasoning_delta(self, delta: str) -> None:
        # If a text bubble is currently being written into, close it —
        # any further reasoning is a new run.
        self._close_text_run()
        if self._reasoning_md is None:
            with self._parent:
                exp = ui.expansion("💭 Thinking", value=True).classes(
                    "rca-reasoning"
                )
                with exp:
                    self._reasoning_md = ui.html("", sanitize=False).classes(
                        "rca-reasoning-content"
                    )
            self._reasoning_buf = []
        self._reasoning_buf.append(delta)
        self._reasoning_md.set_content(
            render_md("".join(self._reasoning_buf))
        )
        if self._on_update:
            self._on_update()

    def add_tool_call(self, name: str, arguments: str) -> None:
        self._close_text_run()
        self._close_reasoning_run()
        args = _truncate(arguments, self._MAX_ARG_LEN)
        head = f"{name}({args})"
        with self._parent:
            with ui.element("div").classes("rca-tool"):
                ui.icon("build").style("font-size:12px;color:#666;")
                label = ui.label(head)
        self._current_tool_label = label
        self._current_tool_head = head
        if self._on_update:
            self._on_update()

    def update_tool_progress(
        self,
        tool_name: str,
        progress: float,
        total: float | None,
        message: str,
    ) -> None:
        """Live-update the last tool chip with a progress fraction
        (`name(args) · 3/10 message`).  No-op if no tool is in flight
        — progress arriving before the first `tool_called` shouldn't
        happen but we guard anyway."""
        if self._current_tool_label is None:
            return
        if total:
            prog = f"{int(progress)}/{int(total)}"
        else:
            prog = f"{progress:g}"
        text = f"{self._current_tool_head} · {prog}"
        if message:
            text += f" — {message}"
        self._current_tool_label.set_text(text)
        if self._on_update:
            self._on_update()

    def add_tool_output(self, name: str, output: str) -> None:
        prefix = f"↳ {name}: " if name else "↳ "
        with self._parent:
            with ui.element("div").classes("rca-tool output"):
                ui.label(prefix + _truncate(output, self._MAX_OUT_LEN))
        # The chip is done; future ProgressEvents (e.g. a stale one
        # straggling in) shouldn't rewrite a finished line.
        self._current_tool_label = None
        self._current_tool_head = ""
        if self._on_update:
            self._on_update()
