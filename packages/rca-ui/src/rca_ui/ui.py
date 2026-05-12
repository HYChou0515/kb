"""NiceGUI chat UI for the RCA agent.

Routes:
    /              — case picker + "New case" form (scans workspace dir)
    /case/<id>     — open + chat in one screen

Cases live under <workspace_root>/<case_id>/case.json. Knowledge ops are
handled by the agent through kb-mcp (stdio); the UI itself makes no
HTTP calls to any KB.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from nicegui import app, ui

from rca_ui.agent import (
    AgentRuntime,
    TextDeltaEvent,
    ToolCallEvent,
    ToolOutputEvent,
    TurnDoneEvent,
)
from rca_ui.config import UISettings
from rca_ui.session_store import (
    AnotherCaseActiveError,
    acquire_active,
    append_transcript,
    read_transcript,
    release_active,
)
from rca_ui.workspace import (
    CaseMeta,
    create_case,
    list_cases,
    open_case,
)

logger = logging.getLogger(__name__)


def register_pages(settings: UISettings) -> None:
    """Wire NiceGUI page handlers. Must be called before ui.run()."""

    @ui.page("/")
    async def index() -> None:
        _install_theme()
        await _render_case_picker(settings)

    @ui.page("/case/{case_id}")
    async def case_page(case_id: str) -> None:
        _install_theme()
        await _render_case_chat(case_id=case_id, settings=settings)


def _install_theme() -> None:
    """Per-page theme: tighten Quasar defaults (q-page padding eats height),
    set a slate background, and pick our accent blue."""
    ui.colors(primary="#2563eb", secondary="#475569", accent="#3b82f6")
    ui.add_head_html(
        "<style>"
        "body{background:#f8fafc;}"
        ".q-page{padding:0!important;}"
        ".rca-bubble{border-radius:1rem;padding:0.65rem 0.9rem;"
        " line-height:1.45;box-shadow:0 1px 2px rgba(15,23,42,0.06);}"
        ".rca-bubble.user{background:#2563eb;color:#fff;}"
        ".rca-bubble.user .q-markdown,.rca-bubble.user *{color:#fff;}"
        ".rca-bubble.assistant{background:#fff;border:1px solid #e2e8f0;color:#0f172a;}"
        ".rca-tool{display:inline-flex;align-items:center;gap:0.35rem;"
        " background:#f1f5f9;border:1px solid #e2e8f0;border-radius:0.5rem;"
        " padding:0.2rem 0.55rem;color:#475569;font:12px/1.4 ui-monospace,SFMono-Regular,monospace;"
        " white-space:pre-wrap;word-break:break-all;}"
        ".rca-tool.output{background:transparent;border:none;color:#64748b;padding-left:1.5rem;}"
        ".rca-file-row{display:flex;align-items:center;gap:0.4rem;"
        " padding:0.3rem 0.55rem;border-radius:0.4rem;cursor:pointer;"
        " font:13px ui-sans-serif,system-ui,sans-serif;color:#334155;}"
        ".rca-file-row:hover{background:#f1f5f9;}"
        ".rca-file-row.selected{background:#dbeafe;color:#1d4ed8;font-weight:500;}"
        ".rca-file-row .name{font-family:ui-monospace,SFMono-Regular,monospace;"
        " font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}"
        "</style>"
    )


# ─── pages ───────────────────────────────────────────────────────────────


async def _render_case_picker(settings: UISettings) -> None:
    with ui.column().classes("w-full max-w-3xl mx-auto px-6 py-8 gap-6"):
        ui.label("RCA Knowledge POC").classes("text-3xl font-semibold tracking-tight")

        # ─── New case form ──────────────────────────────────────────
        with ui.expansion("New case", icon="add").classes(
            "w-full bg-white rounded-xl border border-slate-200"
        ).style("box-shadow: 0 1px 2px rgba(15,23,42,0.04);"):
            with ui.column().classes("w-full gap-3 px-4 pb-4"):
                title_input = ui.input("Title").props("outlined dense").classes("w-full")
                desc_input = (
                    ui.textarea("Description").props("outlined dense").classes("w-full")
                )
                with ui.row().classes("w-full gap-3"):
                    owner_input = (
                        ui.input("Owner").props("outlined dense").classes("flex-grow")
                    )
                    defect_input = (
                        ui.input("Defect type")
                        .props("outlined dense")
                        .classes("flex-grow")
                    )
                with ui.row().classes("w-full gap-3"):
                    module_input = (
                        ui.input("Process module")
                        .props("outlined dense")
                        .classes("flex-grow")
                    )
                    stage_input = (
                        ui.input("Scan stage")
                        .props("outlined dense")
                        .classes("flex-grow")
                    )
                tags_input = (
                    ui.input("Tags (comma-separated)")
                    .props("outlined dense")
                    .classes("w-full")
                )

                async def _create() -> None:
                    title = (title_input.value or "").strip()
                    if not title:
                        ui.notify("Title is required", type="warning")
                        return
                    tags = [
                        t.strip()
                        for t in (tags_input.value or "").split(",")
                        if t.strip()
                    ]
                    meta = create_case(
                        settings.workspace_root,
                        title=title,
                        description=(desc_input.value or "").strip(),
                        owner=(owner_input.value or "unknown").strip(),
                        defect_type=(defect_input.value or "").strip() or None,
                        process_module=(module_input.value or "").strip() or None,
                        scan_stage=(stage_input.value or "").strip() or None,
                        tags=tags,
                    )
                    ui.notify(f"Case created: {meta.id}")
                    ui.navigate.to(f"/case/{meta.id}")

                ui.button("Create case", on_click=_create).props(
                    "color=primary unelevated no-caps"
                ).classes("self-start")

        # ─── List existing ──────────────────────────────────────────
        ui.label("Cases").classes("text-sm font-semibold text-slate-500 uppercase tracking-wider")
        cases = list_cases(settings.workspace_root)

        if not cases:
            ui.label("No cases yet — use “New case” above to create one.").classes(
                "text-sm text-slate-400 italic"
            )
            return

        with ui.column().classes("w-full gap-2"):
            for c in cases:
                with ui.row().classes(
                    "w-full items-center gap-3 bg-white rounded-xl "
                    "border border-slate-200 px-4 py-3 hover:border-blue-300 "
                    "cursor-pointer transition"
                ).style("box-shadow: 0 1px 2px rgba(15,23,42,0.04);").on(
                    "click", lambda _e, cid=c.id: ui.navigate.to(f"/case/{cid}")
                ):
                    with ui.column().classes("flex-grow gap-0 min-w-0"):
                        ui.label(c.title).classes(
                            "font-medium text-slate-900 truncate"
                        )
                        meta_bits = [c.id, f"owner: {c.owner}"]
                        if c.defect_type:
                            meta_bits.append(c.defect_type)
                        if c.status != "active":
                            meta_bits.append(f"status: {c.status}")
                        ui.label(" · ".join(meta_bits)).classes(
                            "text-xs text-slate-500 font-mono truncate"
                        )
                    ui.icon("chevron_right").classes("text-slate-400")


async def _render_case_chat(*, case_id: str, settings: UISettings) -> None:
    # ─── header bar ──────────────────────────────────────────────────
    with ui.row().classes(
        "w-full items-center gap-3 px-4 py-2 bg-white border-b border-slate-200"
    ).style("box-shadow: 0 1px 2px rgba(15,23,42,0.04);"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
            "flat dense round color=grey-8"
        )
        title_label = ui.label("loading…").classes(
            "font-medium text-slate-900 truncate"
        )
        ui.space()
        status_label = ui.label("").classes("text-xs text-slate-500")
        close_btn = ui.button("Close").props(
            "flat dense no-caps color=grey-7 icon=logout"
        )

    # ─── body: splitter (chat | files) ───────────────────────────────
    with ui.splitter(value=64, limits=(30, 85)).classes("w-full bg-white").style(
        "height: calc(100vh - 53px);"
    ) as splitter:
        with splitter.before:
            with ui.column().classes("w-full h-full gap-0 bg-slate-50"):
                chat_scroll = (
                    ui.scroll_area()
                    .classes("w-full px-6 py-4")
                    .style("flex: 1 1 auto; min-height: 0;")
                )
                with chat_scroll:
                    chat_box = ui.column().classes(
                        "w-full max-w-3xl mx-auto gap-3"
                    )
                typing_label = ui.label("").classes(
                    "text-xs text-slate-400 px-6 py-1"
                )
                with ui.row().classes(
                    "w-full items-end gap-2 px-4 py-3 bg-white "
                    "border-t border-slate-200"
                ):
                    input_field = (
                        ui.textarea(placeholder="Type a message — Enter to send")
                        .props("autogrow rows=1 outlined dense")
                        .classes("flex-grow")
                    )
                    send_btn = ui.button(icon="send").props(
                        "color=primary unelevated round"
                    )
        with splitter.after:
            files_container = ui.column().classes(
                "w-full h-full gap-0 bg-white border-l border-slate-200"
            )

    # ─── load case + activate session ────────────────────────────────
    try:
        workspace, meta = open_case(settings.workspace_root, case_id)
    except FileNotFoundError as exc:
        title_label.set_text("not found")
        with chat_box:
            ui.label(str(exc)).classes("text-red-500")
        return

    title_label.set_text(meta.title or case_id)

    try:
        active = await acquire_active(case_id, workspace)
    except AnotherCaseActiveError as exc:
        with chat_box:
            ui.label(str(exc)).classes("text-red-500")
        return

    status_label.set_text("ready (agent boots on first message)")

    # ─── build the file panel inside the right splitter pane ─────────
    with files_container:
        _build_file_panel(workspace)

    # ─── replay transcript into chat box ─────────────────────────────
    for entry in read_transcript(workspace):
        role = entry.get("role")
        content = entry.get("content") or ""
        if role in ("user", "assistant") and content:
            _render_bubble(chat_box, role, content)

    # ─── send handler ────────────────────────────────────────────────
    sending_lock = asyncio.Lock()

    async def _ensure_runtime() -> AgentRuntime:
        runtime = getattr(app.state, "runtime", None)
        if runtime is None:
            model = (
                settings.llm_model
                if settings.llm_provider == "openai"
                else settings.llm_provider_model
            )
            runtime = AgentRuntime(
                workspace_root=settings.workspace_root,
                model=model,
                npx_bin=settings.npx_bin,
            )
            status_label.set_text("booting agent (spawning MCP servers)…")
            await runtime.start()
            app.state.runtime = runtime
        if getattr(app.state, "runtime_case_id", None) != case_id:
            runtime.bind_case(case_id=case_id, workspace=workspace)
            app.state.runtime_case_id = case_id
            prior = read_transcript(workspace)
            if prior:
                history = [
                    {"role": e["role"], "content": e["content"]}
                    for e in prior
                    if e.get("role") in ("user", "assistant") and e.get("content")
                ]
                runtime.load_history(history)
        status_label.set_text("ready")
        return runtime

    async def _send() -> None:
        if sending_lock.locked():
            return
        text = (input_field.value or "").strip()
        if not text:
            return
        input_field.value = ""
        async with sending_lock:
            send_btn.disable()
            typing_label.set_text("agent thinking…")
            _render_bubble(chat_box, "user", text)
            await append_transcript(active, {"role": "user", "content": text})
            view = _AssistantStream(chat_box)
            final_output = ""
            try:
                runtime = await _ensure_runtime()
                async for evt in runtime.run_user_turn_streamed(text):
                    if isinstance(evt, TextDeltaEvent):
                        view.add_text_delta(evt.delta)
                    elif isinstance(evt, ToolCallEvent):
                        view.add_tool_call(evt.name, evt.arguments)
                    elif isinstance(evt, ToolOutputEvent):
                        view.add_tool_output(evt.name, evt.output)
                    elif isinstance(evt, TurnDoneEvent):
                        final_output = evt.final_output
            except Exception as exc:  # noqa: BLE001
                logger.exception("agent turn failed")
                final_output = f"(agent error: {exc.__class__.__name__}: {exc})"
                view.add_text_delta(final_output)
            # Local transcript: write exactly one assistant entry per turn,
            # only after TurnDoneEvent (or exception). KB writes are
            # entirely separate — only fire when the agent explicitly
            # calls kb-mcp.remember during the turn.
            if final_output:
                await append_transcript(
                    active, {"role": "assistant", "content": final_output}
                )
            typing_label.set_text("")
            send_btn.enable()

    send_btn.on_click(_send)
    input_field.on(
        "keydown.enter",
        lambda e: asyncio.create_task(_send()) if not e.args.get("shiftKey") else None,
    )

    # ─── close button ────────────────────────────────────────────────
    async def _close() -> None:
        # Release the active-session lock; the runtime stays warm for the
        # next case open (MCP startup is the slowest step).
        await release_active(case_id, status="closed")
        ui.notify("session closed")
        ui.navigate.to("/")

    close_btn.on_click(_close)


def _render_bubble(parent: Any, role: str, content: str) -> None:
    align = "justify-end" if role == "user" else "justify-start"
    style_cls = "rca-bubble " + ("user" if role == "user" else "assistant")
    with parent:
        with ui.row().classes(f"w-full {align}"):
            with ui.element("div").classes(style_cls).style(
                "max-width: min(80%, 720px);"
            ):
                ui.markdown(content)


class _AssistantStream:
    """Incremental renderer for one streamed assistant turn.

    Lays the turn out top-to-bottom in the chat column:
      🔧 tool-call pill (one per call)
      ↳  tool-output line (one per result, indented)
      [assistant bubble] — appended-to as text deltas arrive

    A tool call closes the current text bubble, so subsequent text deltas
    start a fresh bubble below it. This way the order in which the agent
    interleaves reasoning, tools, and replies is preserved visually.
    """

    _MAX_ARG_LEN = 240
    _MAX_OUT_LEN = 360

    def __init__(self, parent: Any) -> None:
        self._parent = parent
        self._text_md: Any = None
        self._text_buf: list[str] = []

    def add_text_delta(self, delta: str) -> None:
        if self._text_md is None:
            with self._parent:
                with ui.row().classes("w-full justify-start"):
                    with ui.element("div").classes("rca-bubble assistant").style(
                        "max-width: min(80%, 720px);"
                    ):
                        self._text_md = ui.markdown("")
            self._text_buf = []
        self._text_buf.append(delta)
        self._text_md.set_content("".join(self._text_buf))

    def add_tool_call(self, name: str, arguments: str) -> None:
        # Close current text run so the next text delta opens a fresh bubble.
        self._text_md = None
        self._text_buf = []
        args = _truncate(arguments, self._MAX_ARG_LEN)
        with self._parent:
            with ui.row().classes("w-full justify-start"):
                with ui.element("div").classes("rca-tool"):
                    ui.icon("build").classes("text-slate-500").style("font-size:14px;")
                    ui.label(f"{name}({args})")

    def add_tool_output(self, name: str, output: str) -> None:
        prefix = f"↳ {name}: " if name else "↳ "
        with self._parent:
            with ui.row().classes("w-full justify-start"):
                with ui.element("div").classes("rca-tool output"):
                    ui.label(prefix + _truncate(output, self._MAX_OUT_LEN))


def _truncate(s: str, n: int) -> str:
    s = (s or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


# ─── file panel ──────────────────────────────────────────────────────────


_PRIORITY_FILES = (
    "CASE.md",
    "case.json",
    "notes.md",
    "draft_report.md",
    "README.md",
    "transcript.jsonl",
    "session.json",
)

_HIDDEN_PARTS = frozenset({".git", "__pycache__"})

_LANG_BY_SUFFIX: dict[str, str | None] = {
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".json": "JSON",
    ".jsonl": "JSON",
    ".py": "Python",
    ".sh": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".html": "HTML",
    ".css": "CSS",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".sql": "SQL",
}


def _list_workspace_files(workspace: Path) -> list[Path]:
    """Recursively enumerate files under `workspace`, sorted with known
    case files (CASE.md / case.json / notes.md / …) first, then
    alphabetical. Hides .git/ and __pycache__/ subtrees entirely."""
    out: list[Path] = []
    for p in workspace.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(workspace)
        if any(part in _HIDDEN_PARTS for part in rel.parts):
            continue
        out.append(p)

    def _key(p: Path) -> tuple[int, str]:
        rel = str(p.relative_to(workspace))
        try:
            return (_PRIORITY_FILES.index(rel), rel)
        except ValueError:
            return (len(_PRIORITY_FILES), rel)

    return sorted(out, key=_key)


def _detect_lang(path: Path) -> str | None:
    return _LANG_BY_SUFFIX.get(path.suffix.lower())


def _build_file_panel(workspace: Path) -> None:
    """Right-side splitter pane: file list (top) + codemirror editor + actions.
    Caller must be inside an `ui.column` that has `flex: 1 1 auto`-style
    height so the editor fills the available space.
    """
    current: dict[str, Path | None] = {"path": None}

    ui.label("Files").classes("text-sm font-semibold")
    file_list = ui.column().classes("w-full gap-0").style(
        "max-height: 30vh; overflow-y: auto;"
    )
    ui.separator().classes("my-1")
    editor_label = ui.label("(no file selected)").classes(
        "text-xs text-gray-500 truncate font-mono"
    )
    editor = (
        ui.codemirror(value="", line_wrapping=True)
        .classes("w-full")
        .style("flex: 1 1 auto; min-height: 200px;")
    )
    with ui.row().classes("w-full justify-end items-center gap-2"):
        save_btn = ui.button("Save").props("color=primary dense")
        refresh_btn = ui.button(icon="refresh").props("flat dense").tooltip(
            "Refresh file list (use after the agent writes new files)"
        )
    save_btn.disable()

    def _load(path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
            editable = True
        except (UnicodeDecodeError, OSError) as exc:
            content = f"(unreadable: {exc.__class__.__name__}: {exc})"
            editable = False
        current["path"] = path if editable else None
        editor.value = content
        lang = _detect_lang(path)
        try:
            editor.language = lang  # type: ignore[assignment]
        except (AttributeError, ValueError):
            pass
        rel = path.relative_to(workspace)
        editor_label.set_text(str(rel) + ("" if editable else "  (read-only)"))
        if editable:
            save_btn.enable()
        else:
            save_btn.disable()

    def _refresh() -> None:
        file_list.clear()
        with file_list:
            for f in _list_workspace_files(workspace):
                rel = str(f.relative_to(workspace))
                is_current = current["path"] == f
                row = ui.row().classes(
                    "w-full items-center gap-1 cursor-pointer px-1 py-0.5 "
                    + ("bg-blue-50" if is_current else "hover:bg-gray-100")
                )
                with row:
                    ui.icon("description").classes("text-xs text-gray-400")
                    ui.label(rel).classes("text-xs flex-grow truncate font-mono")
                row.on("click", lambda _e, p=f: _load(p))

    def _save() -> None:
        p = current["path"]
        if p is None:
            ui.notify("no file selected", type="warning")
            return
        try:
            p.write_text(editor.value, encoding="utf-8")
            ui.notify(f"saved {p.relative_to(workspace)}", type="positive")
        except OSError as exc:
            ui.notify(f"save failed: {exc}", type="negative")

    save_btn.on_click(_save)
    refresh_btn.on_click(_refresh)
    _refresh()

    # Auto-load CASE.md on open so the panel isn't empty
    case_md = workspace / "CASE.md"
    if case_md.exists():
        _load(case_md)
