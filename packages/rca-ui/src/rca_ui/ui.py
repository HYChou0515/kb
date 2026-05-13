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
import html as html_lib
import io
import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import mistune
from nicegui import app, ui

from rca_ui.agent import (
    AgentRuntime,
    ProgressEvent,
    TextDeltaEvent,
    ToolCallEvent,
    ToolOutputEvent,
    TurnDoneEvent,
)
from rca_ui.config import UISettings
from rca_ui.session_store import (
    append_transcript,
    read_transcript,
)
from rca_ui.workspace import (
    CaseMeta,
    create_case,
    list_cases,
    open_case,
)

logger = logging.getLogger(__name__)


# ─── per-session isolation ───────────────────────────────────────────────
#
# Each browser gets a stable UUID via app.storage.browser (cookie-backed,
# signed by RCA_UI_STORAGE_SECRET).  All workspace I/O — case dirs,
# filesystem MCP root, AgentRuntime — is scoped under that UUID, so two
# concurrent users on the same server never see each other's data.

_SESSION_KEY = "session_id"

# Process-wide registry of per-session runtimes.  AgentRuntime owns long-
# lived MCP subprocesses, so we lazy-spawn it on the user's first message
# and keep it warm for the rest of their session.  Keyed by session_id.
_runtimes: dict[str, AgentRuntime] = {}


def _session_id() -> str:
    """Return this browser's session UUID.  Generates one on first call
    and persists it to the signed browser-cookie storage."""
    sid = app.storage.browser.get(_SESSION_KEY)
    if not sid:
        sid = uuid.uuid4().hex
        app.storage.browser[_SESSION_KEY] = sid
    return sid


def _session_root(settings: UISettings) -> Path:
    """Workspace root for the current browser session.  Cases live as
    `<workspace_root>/<session_id>/<case_id>/`."""
    root = settings.workspace_root / _session_id()
    root.mkdir(parents=True, exist_ok=True)
    return root


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
    """VSCode Light-ish theme. Locks the q-page to viewport height so the
    flex layout below can use 100% without overflow."""
    ui.colors(primary="#0078d4", secondary="#6c6c6c", accent="#0078d4")
    ui.add_head_html(
        "<style>"
        # ─── viewport reset ────────────────────────────────────────
        # NiceGUI wraps content in <main class='q-page nicegui-content'>
        # which ships with padding:1rem + gap:1rem + max width.  Strip
        # all of that so .rca-root can actually fill the viewport.
        "html,body,#q-app,.q-layout,.q-page-container,.q-page,"
        ".nicegui-content"
        "{height:100vh!important;width:100%!important;"
        " overflow:hidden!important;"
        " margin:0!important;padding:0!important;gap:0!important;"
        " max-width:none!important;"
        " font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,"
        "  'Helvetica Neue',Arial,sans-serif;}"
        ".rca-root{display:flex;flex-direction:column;"
        " height:100%;width:100%;"
        " background:#f3f3f3;color:#333;}"
        # ─── title bar ─────────────────────────────────────────────
        ".rca-titlebar{display:flex;align-items:center;gap:8px;"
        " background:#dddddd;border-bottom:1px solid #cecece;"
        " padding:3px 10px;min-height:30px;flex-shrink:0;font-size:12px;color:#333;}"
        ".rca-titlebar .title{font-weight:500;}"
        ".rca-titlebar .status{font-size:11px;color:#6c6c6c;}"
        # ─── body row ──────────────────────────────────────────────
        ".rca-body{display:flex;flex:1 1 auto;min-height:0;width:100%;}"
        # ─── sidebar (file tree) ───────────────────────────────────
        ".rca-sidebar{width:240px;flex-shrink:0;display:flex;"
        " flex-direction:column;background:#f3f3f3;"
        " border-right:1px solid #e5e5e5;}"
        ".rca-section-title{padding:6px 14px 3px;font-size:10px;font-weight:600;"
        " color:#616161;text-transform:uppercase;letter-spacing:0.04em;}"
        ".rca-section-title .toolbtn{cursor:pointer;color:#616161;"
        " padding:2px;border-radius:3px;display:inline-flex;}"
        ".rca-section-title .toolbtn:hover{background:#e0e0e0;}"
        ".rca-tree{flex:1 1 auto;overflow-y:auto;padding:2px 0;}"
        ".rca-file-row{display:flex;align-items:center;gap:5px;"
        " padding:1px 14px;cursor:pointer;user-select:none;color:#424242;"
        " font:12px 'Segoe UI',system-ui,sans-serif;line-height:1.7;}"
        ".rca-file-row:hover{background:#e8e8e8;}"
        ".rca-file-row.selected{background:#e4e6f1;color:#0078d4;}"
        ".rca-file-row .row-icon{font-size:14px;color:#6c6c6c;}"
        ".rca-file-row.selected .row-icon{color:#0078d4;}"
        ".rca-file-row .name{flex:1 1 auto;overflow:hidden;"
        " text-overflow:ellipsis;white-space:nowrap;}"
        # ─── editor area ───────────────────────────────────────────
        ".rca-editor{display:flex;flex-direction:column;width:100%;height:100%;"
        " min-width:0;background:#ffffff;}"
        ".rca-tabbar{display:flex;align-items:stretch;background:#ececec;"
        " border-bottom:1px solid #e5e5e5;min-height:30px;flex-shrink:0;"
        " overflow-x:auto;}"
        ".rca-tab{display:flex;align-items:center;gap:5px;padding:0 8px 0 12px;"
        " cursor:pointer;user-select:none;background:#ececec;color:#6c6c6c;"
        " font:12px 'Segoe UI',system-ui,sans-serif;"
        " border-right:1px solid #e5e5e5;border-top:1px solid transparent;"
        " border-bottom:1px solid transparent;}"
        ".rca-tab .tab-icon{font-size:13px;color:#888;}"
        ".rca-tab .tab-name{white-space:nowrap;}"
        ".rca-tab.active{background:#ffffff;color:#333;"
        " border-top:1px solid #0078d4;border-bottom-color:transparent;}"
        ".rca-tab.dirty .tab-name::before{content:'● ';color:#888;}"
        ".rca-tab .close{visibility:hidden;padding:2px;border-radius:3px;"
        " display:inline-flex;}"
        ".rca-tab:hover .close,.rca-tab.active .close{visibility:visible;}"
        ".rca-tab .close:hover{background:#c8c8c8;}"
        ".rca-tab .close .q-icon{font-size:14px;color:#555;}"
        # ─── view toggle (Source / Preview) sits at right of tab bar ──
        ".rca-view-toggle{margin-left:auto;display:flex;align-items:center;"
        " gap:2px;padding:0 8px;flex-shrink:0;}"
        ".rca-view-btn{display:inline-flex;align-items:center;gap:4px;"
        " padding:2px 7px;cursor:pointer;user-select:none;border-radius:3px;"
        " font:11px 'Segoe UI',system-ui,sans-serif;color:#555;}"
        ".rca-view-btn:hover{background:#dcdcdc;}"
        ".rca-view-btn.active{background:#cce5ff;color:#0078d4;}"
        ".rca-view-btn .q-icon{font-size:13px;}"
        # ─── preview box (md / json / csv read-only views) ────────────
        ".rca-preview-box{flex:1 1 auto;min-height:0;overflow:auto;"
        " background:#ffffff;padding:18px 24px;"
        " font:13px 'Segoe UI',system-ui,sans-serif;color:#1f1f1f;"
        " line-height:1.55;}"
        ".rca-preview-box h1{font-size:22px;margin:0.4em 0 0.3em;"
        " border-bottom:1px solid #eaecef;padding-bottom:0.2em;}"
        ".rca-preview-box h2{font-size:18px;margin:1em 0 0.3em;"
        " border-bottom:1px solid #eaecef;padding-bottom:0.2em;}"
        ".rca-preview-box h3{font-size:15px;margin:0.9em 0 0.3em;}"
        ".rca-preview-box h4,.rca-preview-box h5,.rca-preview-box h6{"
        " font-size:13px;margin:0.8em 0 0.2em;}"
        ".rca-preview-box p{margin:0.4em 0;}"
        ".rca-preview-box ul,.rca-preview-box ol{margin:0.3em 0;padding-left:1.7em;}"
        ".rca-preview-box ul{list-style:disc outside;}"
        ".rca-preview-box ol{list-style:decimal outside;}"
        ".rca-preview-box li{margin:0.15em 0;}"
        ".rca-preview-box code{font:12px ui-monospace,SFMono-Regular,monospace;"
        " background:#f3f3f3;padding:0.1em 0.35em;border-radius:3px;}"
        ".rca-preview-box pre{background:#f6f8fa;border:1px solid #e5e5e5;"
        " border-radius:5px;padding:10px;overflow-x:auto;"
        " font:12px ui-monospace,SFMono-Regular,monospace;line-height:1.45;"
        " white-space:pre;}"
        ".rca-preview-box pre code{background:transparent;padding:0;}"
        ".rca-preview-box blockquote{margin:0.5em 0;padding:0.1em 0.9em;"
        " color:#555;border-left:3px solid #d0d7de;}"
        ".rca-preview-box table{border-collapse:collapse;margin:0.5em 0;"
        " font-size:12px;}"
        ".rca-preview-box th,.rca-preview-box td{"
        " border:1px solid #e5e5e5;padding:4px 10px;text-align:left;}"
        ".rca-preview-box th{background:#f6f8fa;font-weight:600;}"
        ".rca-preview-box tr:nth-child(even) td{background:#fafafa;}"
        ".rca-preview-box a{color:#0078d4;text-decoration:none;}"
        ".rca-preview-box a:hover{text-decoration:underline;}"
        # JSON preview (pretty-printed, monospace, wrapping off)
        ".rca-preview-box.json-mode{padding:14px 18px;background:#fafafa;}"
        ".rca-preview-box.json-mode pre{margin:0;border:0;padding:0;"
        " background:transparent;white-space:pre;font-size:12px;}"
        # CSV table (zebra rows, full-width container scroll)
        ".rca-csv-table{border-collapse:collapse;font:12px ui-monospace,"
        " SFMono-Regular,monospace;}"
        ".rca-csv-table th,.rca-csv-table td{"
        " border:1px solid #e5e5e5;padding:3px 8px;white-space:nowrap;}"
        ".rca-csv-table th{background:#f6f8fa;font-weight:600;text-align:left;}"
        ".rca-csv-table tr:nth-child(even) td{background:#fafafa;}"
        ".rca-preview-empty{color:#9e9e9e;font-style:italic;font-size:12px;}"
        ".rca-editor-host{flex:1 1 auto;min-height:0;display:flex;"
        " flex-direction:column;}"
        ".rca-editor-host > .nicegui-codemirror{flex:1 1 auto;min-height:0;}"
        ".rca-editor-empty{flex:1 1 auto;display:flex;align-items:center;"
        " justify-content:center;color:#9e9e9e;font-size:13px;"
        " font-style:italic;background:#fafafa;}"
        ".rca-statusbar{display:flex;align-items:center;gap:12px;"
        " background:#0078d4;color:#fff;padding:1px 10px;font-size:11px;"
        " min-height:20px;flex-shrink:0;}"
        ".rca-statusbar .savebtn{margin-left:auto;cursor:pointer;"
        " padding:0 6px;border-radius:3px;display:inline-flex;align-items:center;gap:4px;}"
        ".rca-statusbar .savebtn:hover{background:rgba(255,255,255,0.18);}"
        ".rca-statusbar .savebtn[disabled]{opacity:0.5;cursor:default;"
        " pointer-events:none;}"
        # ─── chat panel ────────────────────────────────────────────
        ".rca-chat{display:flex;flex-direction:column;width:100%;height:100%;"
        " background:#f8f8f8;}"
        ".rca-chat-scroll{flex:1 1 auto;min-height:0;}"
        ".rca-chat-list{display:flex;flex-direction:column;gap:10px;"
        " padding:14px 14px 18px;}"
        # q-chat-message bubble color trick: Quasar sets
        # `.q-message-text { background: currentColor }`, then
        # `.q-message-text--received` / `--sent` set `color: <bubble bg>`,
        # then `.q-message-text-content--*` re-sets `color: <real text>`.
        # We override both layers to drive VSCode Light bubbles.
        ".rca-chat .q-message{font-size:12px;margin-bottom:4px;}"
        # Quasar reserves 48px on the last bubble of a message group to
        # align with a 48px avatar.  We don't render avatars, so let the
        # bubble shrink to its content.
        ".rca-chat .q-message-text:last-child{min-height:0;}"
        ".rca-chat .q-message-text--received{color:#ffffff!important;}"
        ".rca-chat .q-message-text-content--received{color:#1f1f1f!important;}"
        ".rca-chat .q-message-text--sent{color:#0078d4!important;}"
        ".rca-chat .q-message-text-content--sent{color:#ffffff!important;}"
        ".rca-chat .q-message-text--received{border:1px solid #e5e5e5;}"
        ".rca-chat .q-message-text{padding:6px 10px;}"
        ".rca-chat .q-message-text-content{line-height:1.45;}"
        ".rca-chat .q-message-name{font-size:10px;color:#666;}"
        # Markdown reset inside bubbles — kill heading h1/h2 bloat
        ".rca-chat .q-message-text-content p{margin:0 0 0.35em;}"
        ".rca-chat .q-message-text-content p:last-child{margin:0;}"
        ".rca-chat .q-message-text-content h1,"
        ".rca-chat .q-message-text-content h2,"
        ".rca-chat .q-message-text-content h3{font-size:13px;margin:0.3em 0;}"
        ".rca-chat .q-message-text-content code{font-size:11.5px;}"
        ".rca-chat .q-message-text-content pre{font-size:11.5px;margin:0.4em 0;}"
        ".rca-chat .q-message-text-content strong{font-weight:700;}"
        ".rca-chat .q-message-text-content em{font-style:italic;}"
        # Quasar resets ul/ol padding → bullets render outside the bubble.
        # Re-establish list indent + markers for both chat and md preview.
        ".rca-chat .q-message-text-content ul,"
        ".rca-chat .q-message-text-content ol{"
        " margin:0.25em 0;padding-left:1.5em;}"
        ".rca-chat .q-message-text-content ul{list-style:disc outside;}"
        ".rca-chat .q-message-text-content ol{list-style:decimal outside;}"
        ".rca-chat .q-message-text-content li{margin:0.1em 0;}"
        ".rca-tool{align-self:flex-start;display:inline-flex;align-items:center;"
        " gap:5px;background:#e8e8e8;border-radius:5px;padding:2px 7px;"
        " color:#444;font:11px/1.45 ui-monospace,SFMono-Regular,monospace;"
        " word-break:break-all;white-space:pre-wrap;max-width:100%;"
        " margin:0 12px;}"
        ".rca-tool.output{background:transparent;color:#666;padding-left:22px;"
        " padding-right:0;font-size:10.5px;}"
        # ─── splitter (editor | chat) ──────────────────────────────
        ".rca-split{flex:1 1 auto;min-width:0;height:100%;}"
        ".rca-split .q-splitter__panel{height:100%;display:flex;}"
        ".rca-split .q-splitter__separator{background:#e5e5e5;width:1px;}"
        ".rca-split .q-splitter__separator-area{width:6px;left:-3px;}"
        ".rca-split .q-splitter__separator-area:hover{background:rgba(0,120,212,0.18);}"
        ".rca-chat-typing{padding:0 12px 3px;font-size:10.5px;color:#888;}"
        ".rca-chat-input{display:flex;align-items:flex-end;gap:6px;"
        " padding:6px;background:#fff;border-top:1px solid #e5e5e5;}"
        ".rca-chat-input .q-textarea{flex:1 1 auto;}"
        ".rca-chat-input .q-field__native{font-size:12px;}"
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
                        _session_root(settings),
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
        cases = list_cases(_session_root(settings))

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
    # ─── root flex column (titlebar + body) ─────────────────────────
    with ui.element("div").classes("rca-root"):

        # ─── title bar ─────────────────────────────────────────────
        with ui.element("div").classes("rca-titlebar"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat dense round size=sm color=grey-9"
            )
            title_label = ui.label("loading…").classes("title")
            ui.element("div").style("flex:1 1 auto;")
            status_label = ui.label("").classes("status")
            close_btn = (
                ui.button(icon="logout")
                .props("flat dense round size=sm color=grey-8")
                .tooltip("Close session")
            )

        # ─── body row (sidebar | editor | chat) ────────────────────
        with ui.element("div").classes("rca-body"):

            # LEFT: file tree
            with ui.element("div").classes("rca-sidebar"):
                with ui.element("div").classes(
                    "rca-section-title"
                ).style("display:flex;align-items:center;justify-content:space-between;"):
                    ui.label("Explorer")
                    refresh_btn = (
                        ui.element("div")
                        .classes("toolbtn")
                        .tooltip("Refresh (after the agent writes new files)")
                    )
                    with refresh_btn:
                        ui.icon("refresh").style("font-size:16px;")
                tree_container = ui.element("div").classes("rca-tree")

            # CENTER + RIGHT: resizable splitter (editor | chat)
            with ui.splitter(value=68, limits=(35, 85)).classes("rca-split") as split:
                with split.before:
                    editor_container = ui.element("div").classes("rca-editor")
                with split.after:
                    with ui.element("div").classes("rca-chat"):
                        with ui.element("div").classes("rca-section-title"):
                            ui.label("Chat")
                        chat_scroll = (
                            ui.scroll_area()
                            .classes("rca-chat-scroll")
                        )
                        with chat_scroll:
                            chat_box = ui.element("div").classes("rca-chat-list")
                        typing_label = ui.label("").classes("rca-chat-typing")
                        with ui.element("div").classes("rca-chat-input"):
                            input_field = (
                                ui.textarea(placeholder="Ask the agent…")
                                .props("autogrow rows=1 outlined dense borderless")
                            )
                            send_btn = (
                                ui.button(icon="send")
                                .props("color=primary unelevated dense round size=sm")
                            )

    # ─── load case (scoped to this browser session) ──────────────────
    session_root = _session_root(settings)
    try:
        workspace, meta = open_case(session_root, case_id)
    except FileNotFoundError as exc:
        title_label.set_text("not found")
        with chat_box:
            ui.label(str(exc)).classes("text-red-500")
        return

    title_label.set_text(meta.title or case_id)
    status_label.set_text("ready (agent boots on first message)")

    # ─── editor + file tree wiring ───────────────────────────────────
    with editor_container:
        editor = _EditorTabs(workspace)

    tree = _FileTree(
        workspace=workspace,
        container=tree_container,
        on_open=editor.open_file,
        is_active=lambda p: editor.active_path() == p,
    )
    editor.set_on_active_changed(tree.refresh)
    tree.refresh()
    refresh_btn.on("click", lambda _e: tree.refresh())

    # Auto-open CASE.md so the editor isn't empty
    case_md = workspace / "CASE.md"
    if case_md.exists():
        editor.open_file(case_md)

    # ─── replay transcript into chat box ─────────────────────────────
    for entry in read_transcript(workspace):
        role = entry.get("role")
        content = entry.get("content") or ""
        if role in ("user", "assistant") and content:
            _render_bubble(chat_box, role, content)
    chat_scroll.scroll_to(percent=1.0)

    # ─── send handler ────────────────────────────────────────────────
    sending_lock = asyncio.Lock()

    sid = _session_id()

    async def _ensure_runtime() -> AgentRuntime:
        runtime = _runtimes.get(sid)
        if runtime is None:
            model = (
                settings.llm_model
                if settings.llm_provider == "openai"
                else settings.llm_provider_model
            )
            # filesystem MCP is sandboxed to this session's directory —
            # no other session's workspace is reachable from this agent.
            runtime = AgentRuntime(
                workspace_root=session_root,
                model=model,
                npx_bin=settings.npx_bin,
                mcp_tool_timeout=settings.mcp_tool_timeout,
            )
            status_label.set_text("booting agent (spawning MCP servers)…")
            await runtime.start()
            _runtimes[sid] = runtime
        if runtime.case_id != case_id:
            runtime.bind_case(case_id=case_id, workspace=workspace)
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

    def _scroll_bottom() -> None:
        chat_scroll.scroll_to(percent=1.0)

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
            _scroll_bottom()
            await append_transcript(workspace, {"role": "user", "content": text})
            view = _AssistantStream(chat_box, on_update=_scroll_bottom)
            final_output = ""
            try:
                runtime = await _ensure_runtime()
                async for evt in runtime.run_user_turn_streamed(text):
                    if isinstance(evt, TextDeltaEvent):
                        view.add_text_delta(evt.delta)
                    elif isinstance(evt, ToolCallEvent):
                        view.add_tool_call(evt.name, evt.arguments)
                    elif isinstance(evt, ProgressEvent):
                        view.update_tool_progress(
                            evt.tool_name, evt.progress, evt.total, evt.message
                        )
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
                    workspace, {"role": "assistant", "content": final_output}
                )
            typing_label.set_text("")
            send_btn.enable()
            _scroll_bottom()

    send_btn.on_click(_send)
    # Enter (no modifiers) → preventDefault stops the textarea's local
    # newline insertion, then submit.  Shift+Enter falls through to the
    # default behavior and inserts a newline as usual.
    input_field.on(
        "keydown.enter.exact.prevent",
        lambda _e: asyncio.create_task(_send()),
    )

    # ─── close button ────────────────────────────────────────────────
    # No process-wide lock to release any more; the per-session runtime
    # stays warm for the next case open in this browser.
    def _close() -> None:
        ui.navigate.to("/")

    close_btn.on_click(_close)


# mistune renders chat markdown server-side.  Plugins:
#   table         — GitHub-style tables
#   strikethrough — ~~strike~~
#   url           — auto-link bare URLs
# CommonMark's right-flanking rule fails on `**lot：**把` (closing **
# between CJK punctuation and CJK letter); mistune is CJK-tolerant
# and renders the <strong> correctly.  Agent output is trusted, so we
# bypass the client-side sanitizer (sanitize=False on ui.html).
_md_render = mistune.create_markdown(plugins=["table", "strikethrough", "url"])


def _render_md(text: str) -> str:
    return _md_render(text or "")


def _render_json_pretty(text: str) -> str:
    """Pretty-print a JSON document as a <pre> block. On parse failure
    returns a short error notice instead of raising."""
    if not (text or "").strip():
        return '<div class="rca-preview-empty">(empty file)</div>'
    try:
        parsed = json.loads(text)
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError) as exc:
        return (
            '<div class="rca-preview-empty">parse failed: '
            f"{html_lib.escape(str(exc))}</div>"
        )
    return f"<pre>{html_lib.escape(pretty)}</pre>"


def _render_jsonl_pretty(text: str) -> str:
    """One pretty-printed block per non-empty JSONL line. Each block is
    prefixed with its 1-based line number; malformed lines are flagged
    inline rather than aborting the whole render."""
    parts: list[str] = []
    for idx, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            pretty = json.dumps(json.loads(line), indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError) as exc:
            pretty = f"(line {idx} parse failed: {exc})"
        parts.append(
            f'<div style="margin-bottom:0.7em;">'
            f'<div style="font:10.5px ui-monospace,monospace;color:#999;'
            f'margin-bottom:2px;">#{idx}</div>'
            f"<pre>{html_lib.escape(pretty)}</pre></div>"
        )
    if not parts:
        return '<div class="rca-preview-empty">(empty file)</div>'
    return "\n".join(parts)


def _render_csv_table(text: str) -> str:
    """Render CSV as an HTML table via pandas. Truncates to 1000 rows
    so a giant CSV doesn't freeze the UI. On parse failure: error notice."""
    if not (text or "").strip():
        return '<div class="rca-preview-empty">(empty file)</div>'
    try:
        import pandas as pd
        df = pd.read_csv(io.StringIO(text))
    except Exception as exc:  # noqa: BLE001 — pandas raises many types
        return (
            '<div class="rca-preview-empty">parse failed: '
            f"{html_lib.escape(str(exc))}</div>"
        )
    total = len(df)
    truncated = ""
    if total > 1000:
        df = df.head(1000)
        truncated = (
            f'<div class="rca-preview-empty">'
            f"showing first 1000 of {total} rows</div>"
        )
    table = df.to_html(
        index=False, classes="rca-csv-table", border=0, escape=True
    )
    return truncated + table


def _render_bubble(parent: Any, role: str, content: str) -> None:
    sent = role == "user"
    name = "You" if sent else "Agent"
    with parent:
        with ui.chat_message(name=name, sent=sent):
            ui.html(_render_md(content), sanitize=False)


class _AssistantStream:
    """Incremental renderer for one streamed assistant turn.

    Appends items into the chat-list flex column in order:
      🔧 tool-call pill (one per call)
      ↳  tool-output line (one per result, indented)
      [assistant bubble] — appended-to as text deltas arrive

    A tool call closes the current text bubble, so subsequent text deltas
    start a fresh bubble below it. Order of interleaving is preserved.
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
        # Last-rendered tool chip — kept around so live ProgressEvents
        # can rewrite its label in place.
        self._current_tool_label: Any = None
        self._current_tool_head: str = ""

    def add_text_delta(self, delta: str) -> None:
        if self._text_md is None:
            with self._parent:
                with ui.chat_message(name="Agent", sent=False):
                    self._text_md = ui.html("", sanitize=False)
            self._text_buf = []
        self._text_buf.append(delta)
        self._text_md.set_content(_render_md("".join(self._text_buf)))
        if self._on_update:
            self._on_update()

    def add_tool_call(self, name: str, arguments: str) -> None:
        self._text_md = None
        self._text_buf = []
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
        (`name(args) · 3/10 message`).  No-op if no tool is in flight —
        progress arriving before the first tool_called shouldn't happen
        but we guard anyway."""
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


class _FileTree:
    """VSCode-style left sidebar: flat list of files under the workspace.
    Click a row → `on_open(path)`. Active row (the one currently open in
    the editor) gets the `selected` class."""

    def __init__(
        self,
        *,
        workspace: Path,
        container: Any,
        on_open: Callable[[Path], None],
        is_active: Callable[[Path], bool],
    ) -> None:
        self._workspace = workspace
        self._container = container
        self._on_open = on_open
        self._is_active = is_active

    def refresh(self) -> None:
        self._container.clear()
        with self._container:
            for f in _list_workspace_files(self._workspace):
                rel = str(f.relative_to(self._workspace))
                cls = "rca-file-row" + (" selected" if self._is_active(f) else "")
                row = ui.element("div").classes(cls)
                with row:
                    ui.icon(_icon_for(f)).classes("row-icon")
                    ui.label(rel).classes("name")
                row.on("click", lambda _e, p=f: self._on_open(p))


def _icon_for(p: Path) -> str:
    suf = p.suffix.lower()
    if suf in (".json", ".jsonl"):
        return "data_object"
    if suf == ".py":
        return "code"
    if suf in (".md", ".markdown"):
        return "article"
    return "insert_drive_file"


_PREVIEW_SUFFIXES = frozenset(
    {".md", ".markdown", ".json", ".jsonl", ".csv"}
)


class _EditorTabs:
    """Center pane: VSCode-style tab bar over one codemirror, with an
    optional read-only preview view for markdown / JSON / CSV files.

    Each open file has an in-memory text buffer; switching tabs flushes
    the editor's current value back into the active buffer and loads the
    next buffer. Save writes the buffer to disk and clears the dirty mark.

    Source / Preview is per-tab state. Toggle lives at the right of the
    tab bar — same control regardless of file type, but the Preview
    button is hidden for non-previewable suffixes.

    Caller must be inside an `ui.element("div").classes("rca-editor")`
    column that fills available height.
    """

    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self._open: list[Path] = []
        self._active: Path | None = None
        self._buffers: dict[Path, str] = {}
        self._disk: dict[Path, str] = {}
        self._modes: dict[Path, Literal["edit", "preview"]] = {}
        self._on_active_changed: Callable[[], None] | None = None

        # Tab bar (tabs + view toggle on right)
        self._tab_bar = ui.element("div").classes("rca-tabbar")
        # Editor host: codemirror OR preview box OR empty placeholder
        self._host = ui.element("div").classes("rca-editor-host")
        with self._host:
            self._empty = ui.element("div").classes("rca-editor-empty")
            with self._empty:
                ui.label("Select a file from the Explorer.")
            self._editor = (
                ui.codemirror(value="", line_wrapping=True, theme="vscodeLight")
                .style("font-size:12px;")
            )
            self._editor.visible = False
            self._preview = ui.element("div").classes("rca-preview-box")
            self._preview.visible = False
        # Status bar
        self._statusbar = ui.element("div").classes("rca-statusbar")
        with self._statusbar:
            self._path_label = ui.label("")
            self._lang_label = ui.label("").style(
                "margin-left:auto;color:rgba(255,255,255,0.85);"
            )
            self._save_link = ui.element("div").classes("savebtn")
            with self._save_link:
                ui.icon("save").style("font-size:14px;")
                ui.label("Save")
            self._save_link.on("click", lambda _e: self._save())
        self._statusbar.visible = False

    def set_on_active_changed(self, fn: Callable[[], None]) -> None:
        self._on_active_changed = fn

    def active_path(self) -> Path | None:
        return self._active

    def open_file(self, path: Path) -> None:
        if path not in self._open:
            try:
                text = path.read_text(encoding="utf-8")
                editable = True
            except (UnicodeDecodeError, OSError) as exc:
                text = f"(unreadable: {exc.__class__.__name__}: {exc})"
                editable = False
            self._buffers[path] = text
            self._disk[path] = text if editable else "\0__binary__\0"  # never matches
            self._open.append(path)
        self._activate(path)

    def _activate(self, path: Path) -> None:
        # Flush previous tab's editor content into its buffer
        if self._active is not None and self._active in self._buffers:
            self._buffers[self._active] = self._editor.value
        self._active = path
        # Restore per-tab mode (default: edit)
        mode = self._modes.setdefault(path, "edit")
        self._empty.visible = False
        self._statusbar.visible = True
        self._editor.value = self._buffers[path]
        lang = _detect_lang(path)
        try:
            self._editor.language = lang  # type: ignore[assignment]
        except (AttributeError, ValueError):
            pass
        rel = path.relative_to(self._workspace)
        self._path_label.set_text(str(rel))
        self._lang_label.set_text(lang or "Plain Text")
        self._apply_mode(mode)
        self._refresh_tabs()
        if self._on_active_changed:
            self._on_active_changed()

    def _apply_mode(self, mode: Literal["edit", "preview"]) -> None:
        """Show editor or preview for the active tab. No-op if no tab."""
        p = self._active
        if p is None:
            return
        if mode == "preview" and p.suffix.lower() not in _PREVIEW_SUFFIXES:
            mode = "edit"
        self._modes[p] = mode
        if mode == "preview":
            self._editor.visible = False
            self._preview.visible = True
            self._render_preview(p)
        else:
            self._preview.visible = False
            self._editor.visible = True

    def _set_mode(self, mode: Literal["edit", "preview"]) -> None:
        # Flush current editor content into buffer before switching out
        if self._active is not None and self._modes.get(self._active) == "edit":
            self._buffers[self._active] = self._editor.value
        self._apply_mode(mode)
        self._refresh_tabs()

    def _render_preview(self, path: Path) -> None:
        """Render the current buffer into self._preview based on suffix.
        Read-only: source of truth is `self._buffers[path]`, not disk."""
        suf = path.suffix.lower()
        text = self._buffers.get(path, "")
        self._preview.clear()
        # Toggle json-mode class (json/jsonl get monospace, off-white bg)
        if suf in (".json", ".jsonl"):
            self._preview.classes(add="json-mode")
        else:
            self._preview.classes(remove="json-mode")
        with self._preview:
            if suf in (".md", ".markdown"):
                ui.html(_render_md(text), sanitize=False)
            elif suf == ".json":
                ui.html(_render_json_pretty(text), sanitize=False)
            elif suf == ".jsonl":
                ui.html(_render_jsonl_pretty(text), sanitize=False)
            elif suf == ".csv":
                ui.html(_render_csv_table(text), sanitize=False)
            else:
                ui.label("(no preview available for this file type)").classes(
                    "rca-preview-empty"
                )

    def _close(self, path: Path) -> None:
        if path not in self._open:
            return
        idx = self._open.index(path)
        self._open.remove(path)
        self._buffers.pop(path, None)
        self._disk.pop(path, None)
        self._modes.pop(path, None)
        if self._active == path:
            if self._open:
                self._activate(self._open[min(idx, len(self._open) - 1)])
            else:
                self._active = None
                self._editor.visible = False
                self._preview.visible = False
                self._statusbar.visible = False
                self._empty.visible = True
                self._refresh_tabs()
                if self._on_active_changed:
                    self._on_active_changed()
        else:
            self._refresh_tabs()

    def _save(self) -> None:
        p = self._active
        if p is None:
            return
        # Editor is the source of truth only when we're actually in edit
        # mode; preview is read-only, buffer already holds the latest.
        if self._modes.get(p, "edit") == "edit":
            self._buffers[p] = self._editor.value
        try:
            p.write_text(self._buffers[p], encoding="utf-8")
        except OSError as exc:
            ui.notify(f"save failed: {exc}", type="negative")
            return
        self._disk[p] = self._buffers[p]
        ui.notify(f"saved {p.relative_to(self._workspace)}", type="positive")
        self._refresh_tabs()

    def _is_dirty(self, p: Path) -> bool:
        if p == self._active and self._modes.get(p, "edit") == "edit":
            return self._editor.value != self._disk.get(p)
        return self._buffers.get(p) != self._disk.get(p)

    def _refresh_tabs(self) -> None:
        self._tab_bar.clear()
        with self._tab_bar:
            for p in self._open:
                is_active = p == self._active
                cls = "rca-tab" + (" active" if is_active else "") + (
                    " dirty" if self._is_dirty(p) else ""
                )
                tab = ui.element("div").classes(cls)
                with tab:
                    ui.icon(_icon_for(p)).classes("tab-icon")
                    ui.label(p.name).classes("tab-name")
                    close = ui.element("div").classes("close")
                    with close:
                        ui.icon("close")
                    close.on(
                        "click", lambda _e, x=p: self._close(x)
                    ).props('@click.stop')
                tab.on("click", lambda _e, x=p: self._activate(x))

            # View toggle at the right of the tab bar.
            if self._active is not None:
                mode = self._modes.get(self._active, "edit")
                supports_preview = (
                    self._active.suffix.lower() in _PREVIEW_SUFFIXES
                )
                with ui.element("div").classes("rca-view-toggle"):
                    edit_cls = "rca-view-btn" + (
                        " active" if mode == "edit" else ""
                    )
                    edit_btn = ui.element("div").classes(edit_cls).tooltip(
                        "Source (editable)"
                    )
                    with edit_btn:
                        ui.icon("edit_note")
                        ui.label("Source")
                    edit_btn.on("click", lambda _e: self._set_mode("edit"))

                    if supports_preview:
                        prev_cls = "rca-view-btn" + (
                            " active" if mode == "preview" else ""
                        )
                        prev_btn = ui.element("div").classes(prev_cls).tooltip(
                            "Preview (read-only)"
                        )
                        with prev_btn:
                            ui.icon("visibility")
                            ui.label("Preview")
                        prev_btn.on(
                            "click", lambda _e: self._set_mode("preview")
                        )
