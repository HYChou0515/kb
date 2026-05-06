"""NiceGUI chat UI for the RCA agent.

Routes:
    /              — case picker (lists cases from kb-api)
    /case/<id>     — open + chat in one screen

Per-tab session state lives on `app.storage.client` (a NiceGUI dict bound
to the SocketIO client connection). For the POC we expect one tab at a
time; the global single-active-session lock in `session_store` enforces it.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from nicegui import app, ui

from rca_ui.agent import AgentRuntime
from rca_ui.config import UISettings
from rca_ui.kb_client import KBClient
from rca_ui.session_store import (
    AnotherCaseActiveError,
    acquire_active,
    append_transcript,
    read_transcript,
    release_active,
)
from rca_ui.workspace import ensure_workspace

logger = logging.getLogger(__name__)


def register_pages(settings: UISettings) -> None:
    """Wire NiceGUI page handlers. Must be called before ui.run()."""
    kb = KBClient(settings.kb_api_base_url)

    @app.on_shutdown
    async def _close_kb() -> None:
        await kb.aclose()

    @ui.page("/")
    async def index() -> None:
        await _render_case_picker(kb)

    @ui.page("/case/{case_id}")
    async def case_page(case_id: str) -> None:
        await _render_case_chat(case_id=case_id, kb=kb, settings=settings)


# ─── pages ───────────────────────────────────────────────────────────────


async def _render_case_picker(kb: KBClient) -> None:
    ui.label("RCA Knowledge POC").classes("text-2xl font-bold")
    ui.label("Pick a case to open its workspace.").classes("text-sm text-gray-500")
    container = ui.column().classes("w-full max-w-3xl gap-2 mt-4")

    try:
        cases = await kb.list_cases()
    except Exception as exc:  # noqa: BLE001
        with container:
            ui.label(f"failed to fetch cases from kb-api: {exc}").classes(
                "text-red-500"
            )
        return

    if not cases:
        with container:
            ui.label("No cases yet. POST a CaseStudy to kb-api first.").classes(
                "text-gray-500"
            )
        return

    with container:
        for case in cases:
            cid = case.get("id") or case.get("resource_id") or ""
            title = case.get("title") or "(untitled)"
            owner = case.get("owner") or "?"
            with ui.card().classes("w-full"):
                ui.label(title).classes("font-semibold")
                ui.label(f"{cid} · owner: {owner}").classes("text-xs text-gray-500")
                ui.button(
                    "Open workspace",
                    on_click=lambda c=cid: ui.navigate.to(f"/case/{c}"),
                )


async def _render_case_chat(
    *, case_id: str, kb: KBClient, settings: UISettings
) -> None:
    """Single-case chat page. Reuses the active AgentRuntime if one is
    already running for this case_id (NiceGUI page reload doesn't tear
    it down); otherwise spawns a new one."""

    # ─── header bar ──────────────────────────────────────────────────
    with ui.row().classes("w-full items-center"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
            "flat"
        )
        title_label = ui.label("loading…").classes("font-semibold text-lg")
        ui.space()
        status_label = ui.label("").classes("text-xs text-gray-500")

    chat_box = ui.column().classes("w-full max-w-4xl gap-2 mt-2 mb-32")
    typing_label = ui.label("").classes("text-xs text-gray-400 ml-2")

    # ─── footer chat bar ─────────────────────────────────────────────
    with ui.footer().classes("bg-white border-t"):
        with ui.row().classes("w-full max-w-4xl mx-auto items-end gap-2 p-2"):
            input_field = (
                ui.textarea(placeholder="Type a message — Enter to send")
                .props("autogrow rows=1 outlined")
                .classes("flex-grow")
            )
            send_btn = ui.button("Send", icon="send")

    # ─── load case + activate session ────────────────────────────────
    try:
        case = await kb.get_case(case_id)
    except Exception as exc:  # noqa: BLE001
        title_label.set_text("failed")
        with chat_box:
            ui.label(f"failed to load case {case_id}: {exc}").classes("text-red-500")
        return

    title_label.set_text(case.get("title") or case_id)

    workspace = ensure_workspace(settings.workspace_root, case_id, case)
    try:
        active = await acquire_active(case_id, workspace)
    except AnotherCaseActiveError as exc:
        with chat_box:
            ui.label(str(exc)).classes("text-red-500")
        return

    status_label.set_text("ready (agent boots on first message)")

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
            try:
                runtime = await _ensure_runtime()
                reply = await runtime.run_user_turn(text)
            except Exception as exc:  # noqa: BLE001
                logger.exception("agent turn failed")
                reply = f"(agent error: {exc.__class__.__name__}: {exc})"
            _render_bubble(chat_box, "assistant", reply)
            await append_transcript(active, {"role": "assistant", "content": reply})
            typing_label.set_text("")
            send_btn.enable()

    send_btn.on_click(_send)
    input_field.on(
        "keydown.enter",
        lambda e: asyncio.create_task(_send()) if not e.args.get("shiftKey") else None,
    )

    # ─── close button ────────────────────────────────────────────────
    async def _close() -> None:
        # Release the active-session lock; the runtime stays warm so the
        # next case open is fast (MCP startup is the slowest step).
        await release_active(case_id, status="closed")
        ui.notify("session closed")
        ui.navigate.to("/")

    with ui.row().classes("absolute top-2 right-2"):
        ui.button("Close session", on_click=_close).props("flat color=warning")


def _render_bubble(parent: Any, role: str, content: str) -> None:
    with parent:
        with ui.row().classes(
            "w-full " + ("justify-end" if role == "user" else "justify-start")
        ):
            with ui.card().classes(
                "max-w-3xl "
                + ("bg-blue-50" if role == "user" else "bg-gray-50")
            ):
                ui.label(role.upper()).classes("text-xs text-gray-400")
                ui.markdown(content)
