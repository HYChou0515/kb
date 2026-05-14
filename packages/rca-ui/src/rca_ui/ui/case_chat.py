"""Case chat page (`/case/<id>`) — three-column VSCode-style layout:
file tree | editor + tabs | chat panel.

This module just wires the panels together and owns the chat send
loop.  Each sub-component is a peer:
- `rca_ui.ui.file_tree.FileTree` — left sidebar
- `rca_ui.ui.editor_view.EditorView` — centre (multi-pane editor)
- `rca_ui.ui.chat.{render_bubble, AssistantStream}` — right chat
- `rca_ui.ui.session._runtimes` — per-session AgentRuntime registry
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from nicegui import ui

from rca_ui.agent import AgentRuntime
from rca_ui.config import UISettings
from rca_ui.session_store import append_transcript, read_transcript
from rca_ui.ui.chat import AssistantStream, render_bubble
from rca_ui.ui.editor_view import EditorView
from rca_ui.ui.file_tree import FileTree
from rca_ui.ui.session import (
    _runtimes,
    current_session_id,
    current_session_root,
)
from rca_ui.workspace import open_case

logger = logging.getLogger(__name__)


async def render_case_chat(*, case_id: str, settings: UISettings) -> None:
    # ─── root flex column (titlebar + body) ─────────────────────────
    with ui.element("div").classes("rca-root"):

        # ─── title bar ─────────────────────────────────────────────
        with ui.element("div").classes("rca-titlebar"):
            ui.button(
                icon="arrow_back", on_click=lambda: ui.navigate.to("/")
            ).props("flat dense round size=sm color=grey-9")
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

            # LEFT: file tree.  FileTree owns the section header (4
            # toolbar buttons) and the tree body; this container is
            # just the flex parent.
            with ui.element("div").classes("rca-sidebar"):
                with ui.element("div").classes("rca-section-title"):
                    ui.label("Explorer")
                tree_container = ui.element("div").classes("rca-tree")

            # CENTER + RIGHT: resizable splitter (editor | chat)
            with ui.splitter(value=68, limits=(35, 85)).classes(
                "rca-split"
            ) as split:
                with split.before:
                    editor_container = ui.element("div").classes("rca-editor")
                with split.after:
                    with ui.element("div").classes("rca-chat"):
                        with ui.element("div").classes("rca-section-title"):
                            ui.label("Chat")
                        chat_scroll = ui.scroll_area().classes("rca-chat-scroll")
                        with chat_scroll:
                            chat_box = ui.element("div").classes("rca-chat-list")
                        typing_label = ui.label("").classes("rca-chat-typing")
                        with ui.element("div").classes("rca-chat-input"):
                            input_field = ui.textarea(
                                placeholder=(
                                    "Ask the agent — Enter to send, "
                                    "Shift+Enter for newline"
                                ),
                            ).props("autogrow rows=1 outlined dense borderless")
                            send_btn = ui.button(icon="send").props(
                                "color=primary unelevated dense round size=sm"
                            )

    # ─── load case (scoped to this browser session) ──────────────────
    session_root = current_session_root(settings)
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
    # `EditorView` owns its EditorLayout + BufferRegistry, persists the
    # split tree to `<workspace>/.editor-layout.json`, and auto-opens
    # CASE.md on first run when no layout file exists yet.
    #
    # NOTE: build the editor BEFORE the tree (the editor's initial
    # render needs `editor_container` ready), then build the tree, then
    # wire the editor's `on_active_changed` to refresh the tree.  The
    # editor's __init__ calls `_render()` which fires the callback —
    # if we pass the callback in the ctor, `tree` is not yet bound and
    # we get a NameError on the first render.
    editor = EditorView(
        workspace=workspace,
        container=editor_container,
    )

    tree = FileTree(
        workspace=workspace,
        container=tree_container,
        on_open=lambda p, preview: editor.open_or_reveal(p, preview=preview),
        is_active=lambda p: editor.active_path() == p,
        is_dirty=editor.is_dirty,
        on_buffer_path_changed=editor.patch_buffer_path,
    )
    def _on_editor_active() -> None:
        # VSCode-style auto-reveal: expand parent folders of the
        # active file and scroll it into view.  Falls back to a
        # plain refresh when no file is active (empty pane).
        active = editor.active_path()
        logger.info("_on_editor_active fired, active=%s", active)
        if active is not None:
            tree.reveal(active)
        else:
            tree.refresh()

    editor.set_on_active_changed(_on_editor_active)
    # Initial reveal so a restored layout pointing at a nested file
    # auto-expands its parent folders on first load.
    _on_editor_active()

    # Ctrl+S / ⌘+S → save active pane's active file.  We pre-empt the
    # browser's "Save Page" dialog via a window-level keydown listener
    # that calls preventDefault before anything else; the actual
    # Python save is wired through `ui.keyboard`.
    # NOTE: only `preventDefault`, NOT `stopPropagation` — capture-
    # phase `stopPropagation` would stop the event from reaching
    # NiceGUI's `ui.keyboard` listener (registered in bubble phase),
    # so the Python save handler would never fire.
    ui.add_body_html(
        "<script>"
        "(function(){"
        " if (window._rca_ctrl_s_installed) return;"
        " window._rca_ctrl_s_installed = true;"
        " document.addEventListener('keydown', function(e){"
        "  if ((e.ctrlKey || e.metaKey) && e.key && e.key.toLowerCase() === 's') {"
        "   e.preventDefault();"
        "  }"
        " }, true);"
        "})();"
        "</script>"
    )

    def _on_key(e: Any) -> None:
        if not e.action.keydown:
            return
        if not (e.modifiers.ctrl or e.modifiers.meta):
            return
        if e.key.code != "KeyS":
            return
        editor.save_active()

    ui.keyboard(on_key=_on_key, repeating=False, ignore=[])

    # ─── replay transcript into chat box ─────────────────────────────
    for entry in read_transcript(workspace):
        role = entry.get("role")
        content = entry.get("content") or ""
        if role in ("user", "assistant") and content:
            render_bubble(chat_box, role, content)
    chat_scroll.scroll_to(percent=1.0)

    # ─── send handler ────────────────────────────────────────────────
    sending_lock = asyncio.Lock()

    sid = current_session_id()

    async def _ensure_runtime() -> AgentRuntime:
        runtime = _runtimes.get(sid)
        if runtime is None:
            model = (
                settings.llm_model
                if settings.llm_provider == "openai"
                else settings.llm_provider_model
            )
            # Filesystem MCP is sandboxed to this session's directory
            # — no other session's workspace is reachable.
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
                    if e.get("role") in ("user", "assistant")
                    and e.get("content")
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
            render_bubble(chat_box, "user", text)
            _scroll_bottom()
            await append_transcript(
                workspace, {"role": "user", "content": text}
            )
            view = AssistantStream(chat_box, on_update=_scroll_bottom)
            final_output = ""
            try:
                runtime = await _ensure_runtime()
                async for evt in runtime.run_user_turn_streamed(text):
                    result = view.handle(evt)
                    if result is not None:
                        final_output = result
            except Exception as exc:  # noqa: BLE001
                logger.exception("agent turn failed")
                final_output = (
                    f"(agent error: {exc.__class__.__name__}: {exc})"
                )
                view.add_text_delta(final_output)
            # Local transcript: write exactly one assistant entry per
            # turn, only after TurnDoneEvent (or exception).  KB writes
            # are entirely separate — only fire when the agent
            # explicitly calls kb-mcp.remember during the turn.
            if final_output:
                await append_transcript(
                    workspace,
                    {"role": "assistant", "content": final_output},
                )
            # Agent likely touched disk — reload every subscribed buffer
            # (clean ones refresh in place; dirty ones keep user edits
            # but get their `disk_text` updated; vanished files flip to
            # deleted-orphan) and re-scan the file tree.
            try:
                editor.post_agent_turn()
                tree.refresh()
            except Exception:  # noqa: BLE001
                logger.exception("post-agent-turn refresh failed")
            typing_label.set_text("")
            send_btn.enable()
            _scroll_bottom()

    send_btn.on_click(_send)
    # Submit on Enter, but let Shift+Enter fall through to the
    # textarea's default newline insertion.  We can't express "Enter
    # without Shift" via NiceGUI's `.on()` modifier syntax — `.exact`
    # isn't in its allowlist (only stop/prevent/self/ctrl/shift/alt/
    # meta), so it gets swallowed and Shift+Enter still fires the
    # handler.  Use a `js_handler` that inspects `shiftKey` client-
    # side: skip when held, otherwise preventDefault + emit to Python.
    input_field.on(
        "keydown.enter",
        lambda _e: asyncio.create_task(_send()),
        js_handler=(
            "(event) => {"
            " if (event.shiftKey) return;"
            " event.preventDefault();"
            " emit(event);"
            "}"
        ),
    )

    # ─── close button ────────────────────────────────────────────────
    # No process-wide lock to release any more; the per-session runtime
    # stays warm for the next case open in this browser.
    def _close() -> None:
        ui.navigate.to("/")

    close_btn.on_click(_close)
