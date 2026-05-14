"""NiceGUI page handlers and UI building blocks for the RCA POC.

Top-level entry point is `register_pages(settings)`; everything else
is internal.  Sub-modules:

- `theme`       — `install_theme()`: per-page CSS + colour palette
- `session`     — per-browser session id, workspace root, runtime
                  registry
- `case_picker` — `/` route handler (case list + "new case" form)
- `case_chat`   — `/case/<id>` route handler (file tree + editor +
                  chat panel)
- `file_tree`   — `FileTree` left-sidebar explorer
- `chat`        — `render_bubble`, `AssistantStream` (chat rendering)
- `editor_view` — `EditorView` (split-tree editor + buffer registry)
- `preview`     — md / json / jsonl / csv read-only renderers
                  shared by the chat bubbles and the editor's
                  Preview view toggle
"""

from __future__ import annotations

from nicegui import ui

from rca_ui.config import UISettings
from rca_ui.ui.case_chat import render_case_chat
from rca_ui.ui.case_picker import render_case_picker
from rca_ui.ui.theme import install_theme


def register_pages(settings: UISettings) -> None:
    """Wire NiceGUI page handlers.  Must be called before
    `ui.run()` in `rca_ui.main`."""

    @ui.page("/")
    async def index() -> None:
        install_theme()
        await render_case_picker(settings)

    @ui.page("/case/{case_id}")
    async def case_page(case_id: str) -> None:
        install_theme()
        await render_case_chat(case_id=case_id, settings=settings)


__all__ = ["register_pages"]
