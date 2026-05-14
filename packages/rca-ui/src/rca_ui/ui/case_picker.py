"""Case picker page (`/`) — lists existing cases for the current
session and lets the user create a new one.

Cases live as directories under `<workspace_root>/<session_id>/`
(see `rca_ui.ui.session.current_session_root`).  This page never
touches the agent or the chat; it just scans the session's workspace
dir, renders the metadata cards, and navigates to `/case/<id>` on
click.
"""

from __future__ import annotations

from nicegui import ui

from rca_ui.config import UISettings
from rca_ui.ui.session import current_session_root
from rca_ui.workspace import create_case, list_cases


async def render_case_picker(settings: UISettings) -> None:
    with ui.column().classes("w-full max-w-3xl mx-auto px-6 py-8 gap-6"):
        ui.label("RCA Knowledge POC").classes(
            "text-3xl font-semibold tracking-tight"
        )

        # ─── New case form ──────────────────────────────────────────
        with ui.expansion("New case", icon="add").classes(
            "w-full bg-white rounded-xl border border-slate-200"
        ).style("box-shadow: 0 1px 2px rgba(15,23,42,0.04);"):
            with ui.column().classes("w-full gap-3 px-4 pb-4"):
                title_input = (
                    ui.input("Title").props("outlined dense").classes("w-full")
                )
                desc_input = (
                    ui.textarea("Description")
                    .props("outlined dense")
                    .classes("w-full")
                )
                with ui.row().classes("w-full gap-3"):
                    owner_input = (
                        ui.input("Owner")
                        .props("outlined dense")
                        .classes("flex-grow")
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
                        current_session_root(settings),
                        title=title,
                        description=(desc_input.value or "").strip(),
                        owner=(owner_input.value or "unknown").strip(),
                        defect_type=(defect_input.value or "").strip() or None,
                        process_module=(module_input.value or "").strip()
                        or None,
                        scan_stage=(stage_input.value or "").strip() or None,
                        tags=tags,
                    )
                    ui.notify(f"Case created: {meta.id}")
                    ui.navigate.to(f"/case/{meta.id}")

                ui.button("Create case", on_click=_create).props(
                    "color=primary unelevated no-caps"
                ).classes("self-start")

        # ─── List existing ──────────────────────────────────────────
        ui.label("Cases").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider"
        )
        cases = list_cases(current_session_root(settings))

        if not cases:
            ui.label(
                "No cases yet — use “New case” above to create one."
            ).classes("text-sm text-slate-400 italic")
            return

        with ui.column().classes("w-full gap-2"):
            for c in cases:
                with ui.row().classes(
                    "w-full items-center gap-3 bg-white rounded-xl "
                    "border border-slate-200 px-4 py-3 hover:border-blue-300 "
                    "cursor-pointer transition"
                ).style(
                    "box-shadow: 0 1px 2px rgba(15,23,42,0.04);"
                ).on(
                    "click",
                    lambda _e, cid=c.id: ui.navigate.to(f"/case/{cid}"),
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
