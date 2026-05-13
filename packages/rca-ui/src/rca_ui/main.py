"""rca_ui entrypoint — boots NiceGUI on its own port.

Runs in a sibling process to kb-api. Talks to kb-api via HTTP for typed
records (CaseStudy / RCAReport / etc.); spawns its own MCP servers as
stdio subprocesses for the agent's tool surface.

Run:
    uv run rca-ui

Or via the demo orchestrator (./scripts/demo.sh).
"""

from __future__ import annotations

import logging

from nicegui import ui

from rca_ui.config import load_ui_settings
from rca_ui.ui import register_pages


def run() -> None:
    settings = load_ui_settings()
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    register_pages(settings)
    ui.run(
        host=settings.ui_host,
        port=settings.ui_port,
        title="RCA Knowledge POC",
        reload=False,
        show=False,
        # Needed by app.storage.browser — we use it to assign a stable
        # per-browser session UUID that scopes each user's workspace dir.
        storage_secret=settings.storage_secret,
    )


if __name__ in {"__main__", "__mp_main__"}:
    run()
