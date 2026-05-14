"""NiceGUI rendering layer for the recursive split editor.

`EditorView` is a thin VIEW over `EditorLayout` + `BufferRegistry`.  It
owns no business logic — every mutation goes through the data model,
then the view re-renders.  This split keeps the data layer testable
(see `tests/test_editor_layout.py`, `tests/test_buffer_registry.py`)
while the UI layer can be eyeballed manually in the browser.

Layout shape:
    ┌─ rca-editor-host ───────────────────────────────────────┐
    │ ui.splitter (recursive, one per _Split node)            │
    │  ├─ before/after = leaf pane OR another splitter        │
    │  └─ each leaf pane = .rca-pane                          │
    │       ┌─ .rca-tabbar (tabs + view toggle)               │
    │       ├─ codemirror OR preview box                      │
    │       └─ .rca-statusbar                                 │
    └──────────────────────────────────────────────────────────┘

Phase-2 scope:
  - recursive render
  - click-to-focus active pane
  - open_or_reveal from Explorer
  - close tab × button (no modal yet — comes next)
  - dirty ● indicator
  - Save link in status bar
  - persistence to `<workspace>/.editor-layout.json`

Not yet here (Phase 2b):
  - drag-and-drop split / move / clone
  - right-click context menu
  - close-confirm dialog
  - Ctrl+S global hook
  - shared-buffer codemirror sync on edit
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from nicegui import ui

from rca_ui.buffer_registry import BufferRegistry
from rca_ui.editor_layout import EditorLayout
from rca_ui.ui.preview import is_previewable, render_for_path

logger = logging.getLogger(__name__)

_LAYOUT_FILE = ".editor-layout.json"

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


def _detect_lang(path: Path) -> str | None:
    return _LANG_BY_SUFFIX.get(path.suffix.lower())


def _icon_for(p: Path) -> str:
    suf = p.suffix.lower()
    if suf in (".json", ".jsonl"):
        return "data_object"
    if suf == ".py":
        return "code"
    if suf in (".md", ".markdown"):
        return "article"
    return "insert_drive_file"


class EditorView:
    """Top-level view for the split editor area.

    `container` is the `ui.element` to render the tree into; the
    constructor wipes it and rebuilds.  `on_active_changed` fires
    whenever the active pane / active tab changes, useful for the file
    tree's selection highlight."""

    def __init__(
        self,
        *,
        workspace: Path,
        container: Any,
        on_active_changed: Callable[[], None] | None = None,
    ) -> None:
        self._workspace = workspace
        self._container = container
        self._on_active_changed = on_active_changed
        # While True, `_on_cm_change` ignores incoming codemirror
        # change events.  Set during every `_render()` so spurious
        # `update:value` events that fire during Vue's
        # mount/unmount transition (e.g. right after a split) don't
        # poison the buffer's current_text.  Re-enabled by a short
        # timer once the new DOM tree has settled.
        self._rendering = True

        # Per-pane Vue element references — populated by _render(),
        # cleared on each re-render.  `tab_bar` is the row above the
        # editor, `host` holds codemirror + preview-box, and
        # `codemirror` / `preview_box` are toggled by Source/Preview.
        self._pane_widgets: dict[str, dict[str, Any]] = {}
        # Per-pane view mode (Source vs Preview).  Persisted across
        # re-renders within the session so toggling Preview survives
        # an `_activate_tab`-triggered re-render.  Reset to default
        # ('edit') the first time a pane is rendered.
        self._pane_modes: dict[str, str] = {}

        # Disk I/O is injected into BufferRegistry so tests don't need
        # a real workspace.  Here we use Path.read_text / write_text
        # on the case workspace.
        self._registry = BufferRegistry(
            read_disk=self._read_disk,
            write_disk=self._write_disk,
            on_change=self._on_buffer_change,
        )

        # Either restore from `.editor-layout.json` or seed with a
        # single-pane layout and auto-open CASE.md if present.
        self._layout = self._load_or_init_layout()

        # Subscribe all already-open files to BufferRegistry so the
        # status-bar dirty marker and save link work from the start.
        for pid in self._all_pane_ids():
            for path in self._layout.pane(pid).open_files:
                self._registry.subscribe(path, pid)

        self._render()

    # ─── public API the rest of ui.py calls ──────────────────────────

    def open_or_reveal(self, path: Path, preview: bool = False) -> None:
        """Explorer-click entry point — jump to existing tab or open
        in the active pane.

        `preview=True` (single-click from the file tree) makes the
        opened tab the pane's preview slot: a subsequent single-click
        on another file replaces this tab in place rather than
        stacking a new one.  `preview=False` (double-click, agent
        autoreveal, Enter key) is the normal persistent open.

        Layout-side semantics live in `EditorLayout.open_or_reveal`;
        this wrapper just subscribes new files and triggers a render.
        """
        is_new = not any(
            path in self._layout.pane(pid).open_files
            for pid in self._all_pane_ids()
        )
        pid = self._layout.open_or_reveal(path, preview=preview)
        if is_new:
            self._registry.subscribe(path, pid)
        self._persist()
        self._render()

    def patch_buffer_path(self, old: Path, new: Path | None) -> None:
        """File-tree hook: a file on disk has been renamed / moved /
        deleted.  Reconcile open tabs:

        - `new` is None → file gone → mark buffer deleted, keep tab as
          strike-through orphan.
        - `new` is given → rename the path in both EditorLayout
          (rewrite every pane's tab list) and BufferRegistry (move
          buffer state under the new key).
        """
        if new is None:
            self._registry.mark_deleted(old)
            self._render()
            return
        self._layout.rename_path(old, new)
        self._registry.rename_path(old, new)
        self._persist()
        self._render()

    def is_dirty(self, path: Path) -> bool:
        """Exposed so the file tree can warn before destructive ops."""
        return self._registry.is_dirty(path)

    def post_agent_turn(self) -> None:
        """Re-read disk for every subscribed buffer.  Clean buffers
        adopt new disk content; dirty buffers keep the user's edits
        but pick up the new `disk_text` (so `is_dirty` reflects the
        diff against the latest disk state); missing files flip to
        deleted."""
        for path in self._registry.subscribed_paths():
            self._registry.reload_disk_text(path)

    def set_on_active_changed(
        self, callback: Callable[[], None] | None
    ) -> None:
        """Late-bind the active-changed observer.  Use this when the
        callback closes over something (e.g. the file tree) that's
        constructed AFTER `EditorView`."""
        self._on_active_changed = callback

    def active_path(self) -> Path | None:
        pid = self._layout.active_pane_id
        if pid not in self._panes_dict():
            return None
        return self._layout.pane(pid).active_file

    def save_active(self) -> None:
        """Save the active pane's active file.  No-op when the pane is
        empty or there's no readable file in focus.  Bound to Ctrl+S
        from `ui.py`."""
        pid = self._layout.active_pane_id
        if pid not in self._panes_dict():
            return
        path = self._layout.pane(pid).active_file
        if path is None:
            return
        try:
            self._registry.save(path)
        except OSError as exc:
            ui.notify(f"save failed: {exc}", type="negative")
            return
        rel = (
            path.relative_to(self._workspace)
            if self._workspace in path.parents
            else path
        )
        ui.notify(f"saved {rel}", type="positive")
        # No full re-render — that would destroy codemirror state and
        # the user's cursor position.  Just flip the tab's dirty class.
        self._refresh_dirty(path)

    # ─── render ──────────────────────────────────────────────────────

    def _render(self) -> None:
        self._rendering = True
        self._container.clear()
        self._pane_widgets = {}
        blob = self._layout.to_dict()
        # Everything below — including the on_active_changed callback —
        # MUST run inside `with self._container:` so the NiceGUI slot
        # context is alive.  When `_render` runs from a click handler
        # (e.g. `_activate_tab` or a tab close), the current slot is
        # the clicked element's slot, and `self._container.clear()`
        # just destroyed it.  Anything that touches the slot (e.g.
        # `ui.timer`, or the file tree's `ui.run_javascript` inside
        # its `reveal`) blows up with "parent slot has been deleted",
        # aborting the render and swallowing the callback.
        # Re-opening `with self._container` establishes a live slot
        # (the container itself is preserved across clear()).
        with self._container:
            self._render_node(blob["root"])
            ui.timer(0.2, self._release_rendering_gate, once=True)
            if self._on_active_changed:
                self._on_active_changed()

    def _release_rendering_gate(self) -> None:
        self._rendering = False

    def _render_node(self, node: dict[str, Any]) -> None:
        if node["type"] == "leaf":
            self._render_pane(node["pane_id"])
            return
        # Split node — Quasar's q-splitter is binary, matches our model.
        assert len(node["children"]) == 2, "splits are 2-ary by design"
        horizontal = node["direction"] == "vertical"
        value = node["ratios"][0]
        with ui.splitter(
            value=value, horizontal=horizontal, limits=(10, 90)
        ).classes("rca-editor-split").style(
            "width:100%;height:100%;"
        ) as splitter:
            with splitter.before:
                self._render_node(node["children"][0])
            with splitter.after:
                self._render_node(node["children"][1])
            # Resize-persistence: Quasar keeps the splitter's value in
            # its own state for the current render, but on the next
            # reload we'd reset to 50/50 because the layout JSON's
            # ratios aren't updated.  Wiring resize → set_pane_ratio
            # needs split-node identity in the model (not yet exposed)
            # — Phase 2c follow-up.  Drag still works visually within
            # the session.

    def _render_pane(self, pane_id: str) -> None:
        pane = self._layout.pane(pane_id)
        is_active = self._layout.active_pane_id == pane_id
        pane_div = ui.element("div").classes(
            "rca-pane" + (" rca-pane-active" if is_active else "")
        )
        pane_div.on("click", lambda _e, pid=pane_id: self._activate(pid))
        # Set up the widget map first so `_render_tabs` can write
        # per-tab references into it as it iterates.  Overwriting the
        # whole dict at the END would discard those refs.
        self._pane_widgets[pane_id] = {
            "pane_div": pane_div,
            "tab_bar": None,
            "host": None,
            "codemirror": None,
            "preview_box": None,
            "tabs": {},
        }
        # Wire the pane as a drag-drop target: dragover shows the
        # prospective drop zone via a CSS overlay (set via data-attr);
        # drop emits to Python which performs the actual move / split /
        # clone via the data model.  `js_handler` writes to attributes
        # so CSS can react without per-event Python round trips.
        pane_div.on(
            "dragover",
            None,
            js_handler=(
                "(event) => {"
                " event.preventDefault();"
                " const rect = event.currentTarget.getBoundingClientRect();"
                " const x = (event.clientX - rect.left) / rect.width;"
                " const y = (event.clientY - rect.top) / rect.height;"
                ' let zone = "center";'
                ' if (x < 0.1) zone = "left";'
                ' else if (x > 0.9) zone = "right";'
                ' else if (y < 0.1) zone = "top";'
                ' else if (y > 0.9) zone = "bottom";'
                # Clone modifier: Alt (⌥) on macOS, Ctrl on Windows /
                # Linux — matches VSCode's convention.  We also accept
                # Ctrl on macOS for parity and Meta (⌘) as a fallback
                # for browsers that happen to forward it, but Alt is
                # the primary native-feeling shortcut on a Mac.
                " const clone ="
                "  event.altKey || event.ctrlKey || event.metaKey;"
                ' event.currentTarget.setAttribute("data-drop-zone", zone);'
                ' event.currentTarget.setAttribute('
                '  "data-drop-ctrl", clone ? "1" : "0"'
                " );"
                ' event.dataTransfer.dropEffect = clone ? "copy" : "move";'
                "}"
            ),
        )
        pane_div.on(
            "dragleave",
            None,
            js_handler=(
                "(event) => {"
                " if (event.relatedTarget && event.currentTarget.contains(event.relatedTarget)) return;"
                ' event.currentTarget.removeAttribute("data-drop-zone");'
                ' event.currentTarget.removeAttribute("data-drop-ctrl");'
                "}"
            ),
        )
        pane_div.on(
            "drop",
            lambda e, pid=pane_id: self._handle_drop(pid, e.args),
            js_handler=(
                "(event) => {"
                " event.preventDefault();"
                ' const dt = event.dataTransfer.getData("text/plain");'
                # Read the ctrl/meta state captured by the most recent
                # dragover before clearing the data attrs.  On macOS
                # some browsers strip `metaKey` from the `drop` event
                # itself (the OS reserves ⌘ for drag-effect alias),
                # so relying on `event.metaKey` here misses Cmd-drag.
                " const ctrlAttr ="
                '  event.currentTarget.getAttribute("data-drop-ctrl") === "1";'
                ' event.currentTarget.removeAttribute("data-drop-zone");'
                ' event.currentTarget.removeAttribute("data-drop-ctrl");'
                " if (!dt) return;"
                " const data = JSON.parse(dt);"
                " const rect = event.currentTarget.getBoundingClientRect();"
                " const x = (event.clientX - rect.left) / rect.width;"
                " const y = (event.clientY - rect.top) / rect.height;"
                ' let zone = "center";'
                ' if (x < 0.1) zone = "left";'
                ' else if (x > 0.9) zone = "right";'
                ' else if (y < 0.1) zone = "top";'
                ' else if (y > 0.9) zone = "bottom";'
                " emit({"
                "  type: data.type || null,"
                "  source_pane: data.pane,"
                "  source_path: data.path,"
                "  zone: zone,"
                "  ctrl: ctrlAttr || event.altKey || event.ctrlKey || event.metaKey"
                " });"
                "}"
            ),
        )
        with pane_div:
            tab_bar = ui.element("div").classes("rca-tabbar")
            self._render_tabs(tab_bar, pane_id, pane.open_files, pane.active_file)
            host = ui.element("div").classes("rca-editor-host")
            with host:
                preview_box = None
                if pane.active_file is None:
                    with ui.element("div").classes("rca-editor-empty"):
                        ui.label("Select a file from the Explorer.")
                    codemirror = None
                else:
                    text = self._registry.text(pane.active_file)
                    lang = _detect_lang(pane.active_file)
                    mode = self._pane_modes.setdefault(pane_id, "edit")
                    # Force edit mode for files we don't have a
                    # preview renderer for (e.g. .py / .txt).
                    if mode == "preview" and not is_previewable(pane.active_file):
                        mode = "edit"
                        self._pane_modes[pane_id] = "edit"
                    # IMPORTANT: use NiceGUI's `on_change=` callback,
                    # not `.on('update:model-value', ...)`.  The raw
                    # Vue event name codemirror emits is internal and
                    # not bound by the Python wrapper — the only
                    # supported edit-hook is `on_change`.
                    # `cm_state["ready"]` is False until the user
                    # actually focuses this codemirror.  Until then we
                    # drop every `on_change` emission — there's no
                    # such thing as a user-driven edit before focus,
                    # so anything that fires must be a Vue
                    # render-transition artefact and must not be
                    # written back to the buffer.
                    cm_state = {"ready": False}
                    codemirror = ui.codemirror(
                        value=text,
                        line_wrapping=True,
                        theme="vscodeLight",
                        language=lang,  # type: ignore[arg-type]
                        on_change=(
                            lambda e, p=pane.active_file, s=cm_state: (
                                None
                                if not s["ready"]
                                else self._on_cm_change(p, e.value)
                            )
                        ),
                    ).style("font-size:12px;")
                    codemirror.on(
                        "focusin",
                        lambda _e, s=cm_state: s.update(ready=True),
                    )
                    # Preview box sits alongside the codemirror in the
                    # editor host; only one is visible at a time per
                    # `_pane_modes`.
                    preview_box = ui.element("div").classes("rca-preview-box")
                    if is_previewable(pane.active_file):
                        suf = pane.active_file.suffix.lower()
                        if suf in (".json", ".jsonl"):
                            preview_box.classes(add="json-mode")
                    with preview_box:
                        ui.html(
                            render_for_path(pane.active_file, text),
                            sanitize=False,
                        )
                    codemirror.visible = mode == "edit"
                    preview_box.visible = mode == "preview"
            # Status bar is always rendered when there is an active
            # file; CSS hides it for inactive panes so click-to-focus
            # can swap which pane "owns" the status line via a CSS
            # class toggle, no re-render needed.
            if pane.active_file is not None:
                self._render_statusbar(pane_id, pane.active_file)
        # Finalise the entry without clobbering `tabs` (which was
        # populated by `_render_tabs`).
        self._pane_widgets[pane_id].update(
            tab_bar=tab_bar,
            host=host,
            codemirror=codemirror,
            preview_box=preview_box,
        )

    def _render_tabs(
        self,
        tab_bar: Any,
        pane_id: str,
        open_files: tuple[Path, ...],
        active_file: Path | None,
    ) -> None:
        # Reset the tab-ref cache for this pane; `_refresh_dirty` reads
        # from here to flip class state without re-rendering.
        self._pane_widgets.setdefault(pane_id, {})["tabs"] = {}
        # The pane's preview slot — at most one path per pane.  We
        # fetch it once outside the loop to avoid a pane() call per tab.
        pane_view = self._layout.pane(pane_id)
        preview_file = pane_view.preview_file
        with tab_bar:
            for path in open_files:
                is_active = path == active_file
                dirty = self._registry.is_dirty(path)
                deleted = self._registry.is_deleted(path)
                cls = "rca-tab"
                if is_active:
                    cls += " active"
                if dirty:
                    cls += " dirty"
                if deleted:
                    cls += " deleted"
                if preview_file is not None and path == preview_file:
                    cls += " preview"
                tab = ui.element("div").classes(cls)
                tab.props("draggable=true")
                tab.on(
                    "dragstart",
                    None,
                    js_handler=(
                        "(event) => {"
                        ' event.dataTransfer.setData("text/plain", JSON.stringify({'
                        f"  pane: {json.dumps(pane_id)},"
                        f"  path: {json.dumps(str(path))}"
                        " }));"
                        ' event.dataTransfer.effectAllowed = "copyMove";'
                        "}"
                    ),
                )
                with tab:
                    ui.icon(_icon_for(path)).classes("tab-icon")
                    ui.label(path.name).classes("tab-name")
                    close = ui.element("div").classes("close")
                    with close:
                        # Render both icons; CSS shows ● when the
                        # parent `.rca-tab` has `.dirty`, and × on
                        # hover (or when clean).  This lets us flip
                        # the dirty state purely by toggling a class
                        # on the tab from `_refresh_dirty`, with no
                        # need to re-render the icon DOM.
                        ui.icon("fiber_manual_record").classes("dirty-icon")
                        ui.icon("close").classes("close-icon")
                    # NiceGUI's modifier system on `.on()` is the
                    # supported way to add Vue's `.stop` modifier.
                    # `.props("@click.stop")` looks like a Vue
                    # template binding but it's actually parsed as a
                    # plain HTML attribute (`stop="true"` shows up in
                    # the DOM) — propagation isn't stopped, the click
                    # bubbles to the tab and re-activates it,
                    # erasing the close + modal.
                    close.on(
                        "click.stop",
                        lambda _e, pid=pane_id, p=path: self._close_tab(pid, p),
                    )
                    # Right-click context menu — same 6 entries as VSCode.
                    with ui.context_menu():
                        ui.menu_item(
                            "Close",
                            lambda _e=None, pid=pane_id, p=path: self._close_tab(
                                pid, p
                            ),
                        )
                        ui.menu_item(
                            "Close Others",
                            lambda _e=None, pid=pane_id, p=path: self._close_others(
                                pid, p
                            ),
                        )
                        ui.menu_item(
                            "Close to the Left",
                            lambda _e=None, pid=pane_id, p=path: self._close_to_left(
                                pid, p
                            ),
                        )
                        ui.menu_item(
                            "Close to the Right",
                            lambda _e=None, pid=pane_id, p=path: self._close_to_right(
                                pid, p
                            ),
                        )
                        ui.separator()
                        ui.menu_item(
                            "Close Saved",
                            lambda _e=None, pid=pane_id: self._close_saved(pid),
                        )
                        ui.menu_item(
                            "Close All",
                            lambda _e=None, pid=pane_id: self._close_all(pid),
                        )
                tab.on(
                    "click",
                    lambda _e, pid=pane_id, p=path: self._activate_tab(pid, p),
                )
                self._pane_widgets[pane_id]["tabs"][path] = tab
            # Source / Preview view toggle at the right end of the
            # tab bar.  Preview button is hidden for file types that
            # have no read-only preview renderer.
            if active_file is not None:
                self._render_view_toggle(pane_id, active_file)

    def _render_view_toggle(self, pane_id: str, active_file: Path) -> None:
        mode = self._pane_modes.get(pane_id, "edit")
        supports_preview = is_previewable(active_file)
        with ui.element("div").classes("rca-view-toggle"):
            edit_cls = "rca-view-btn" + (" active" if mode == "edit" else "")
            edit_btn = (
                ui.element("div").classes(edit_cls).tooltip("Source (editable)")
            )
            with edit_btn:
                ui.icon("edit_note")
                ui.label("Source")
            edit_btn.on(
                "click.stop",
                lambda _e, pid=pane_id: self._set_mode(pid, "edit"),
            )
            if supports_preview:
                prev_cls = "rca-view-btn" + (
                    " active" if mode == "preview" else ""
                )
                prev_btn = (
                    ui.element("div")
                    .classes(prev_cls)
                    .tooltip("Preview (read-only)")
                )
                with prev_btn:
                    ui.icon("visibility")
                    ui.label("Preview")
                prev_btn.on(
                    "click.stop",
                    lambda _e, pid=pane_id: self._set_mode(pid, "preview"),
                )

    def _set_mode(self, pane_id: str, mode: str) -> None:
        """Toggle a pane between Source (codemirror) and Preview
        (read-only render).  Updates DOM in place — no `_render()` —
        so codemirror state is preserved across mode flips."""
        pane = self._layout.pane(pane_id)
        if pane.active_file is None:
            return
        if mode == "preview" and not is_previewable(pane.active_file):
            return
        self._pane_modes[pane_id] = mode
        widgets = self._pane_widgets.get(pane_id, {})
        cm = widgets.get("codemirror")
        preview_box = widgets.get("preview_box")
        if cm is not None:
            cm.visible = mode == "edit"
        if preview_box is not None:
            preview_box.visible = mode == "preview"
            if mode == "preview":
                text = self._registry.text(pane.active_file)
                preview_box.clear()
                with preview_box:
                    ui.html(
                        render_for_path(pane.active_file, text),
                        sanitize=False,
                    )
        # Re-render just the tab bar to refresh the active class on
        # the toggle buttons.
        tab_bar = widgets.get("tab_bar")
        if tab_bar is not None:
            tab_bar.clear()
            self._render_tabs(
                tab_bar, pane_id, pane.open_files, pane.active_file
            )

    def _refresh_dirty(self, path: Path) -> None:
        """Update the `.dirty` class on every tab whose file is `path`.
        Called whenever the buffer's clean/dirty state may have changed
        (`set_text` broadcasts, save completes).  Avoids a full
        re-render so codemirror keeps its cursor / scroll / focus."""
        dirty = self._registry.is_dirty(path)
        for widgets in self._pane_widgets.values():
            tab = widgets.get("tabs", {}).get(path)
            if tab is None:
                continue
            if dirty:
                tab.classes(add="dirty")
            else:
                tab.classes(remove="dirty")

    def _render_statusbar(self, pane_id: str, path: Path) -> None:
        with ui.element("div").classes("rca-statusbar"):
            rel = path.relative_to(self._workspace) if (
                self._workspace in path.parents or path == self._workspace
            ) else path
            ui.label(str(rel))
            lang = _detect_lang(path) or "Plain Text"
            ui.label(lang).style(
                "margin-left:auto;color:rgba(255,255,255,0.85);"
            )
            save_btn = ui.element("div").classes("savebtn")
            with save_btn:
                ui.icon("save").style("font-size:12px;")
                ui.label("Save")
            save_btn.on(
                "click", lambda _e, pid=pane_id, p=path: self._save(pid, p)
            )

    # ─── event handlers ─────────────────────────────────────────────

    def _activate(self, pane_id: str) -> None:
        """Click-to-focus.  We must NOT trigger a full re-render here
        — every codemirror would be destroyed and any pending edits
        (still in flight from the client) would be lost.  Just toggle
        the `.rca-pane-active` CSS class on the two affected panes;
        the status bar visibility follows via CSS."""
        if pane_id == self._layout.active_pane_id:
            return
        if pane_id not in self._panes_dict():
            return
        old_pid = self._layout.active_pane_id
        self._layout._active_pane_id = pane_id  # type: ignore[attr-defined]
        old_widgets = self._pane_widgets.get(old_pid)
        if old_widgets is not None:
            old_widgets["pane_div"].classes(remove="rca-pane-active")
        new_widgets = self._pane_widgets.get(pane_id)
        if new_widgets is not None:
            new_widgets["pane_div"].classes(add="rca-pane-active")
        self._persist()
        if self._on_active_changed:
            self._on_active_changed()

    def _activate_tab(self, pane_id: str, path: Path) -> None:
        # Reuse open_file semantics — re-focuses if already open.
        self._layout.open_file(pane_id, path)
        self._persist()
        self._render()

    def _close_tab(self, pane_id: str, path: Path) -> None:
        self._guarded_close([(pane_id, path)], lambda: self._do_close_tab(pane_id, path))

    def _close_others(self, pane_id: str, anchor: Path) -> None:
        doomed = [
            p for p in self._layout.pane(pane_id).open_files if p != anchor
        ]
        self._guarded_close(
            [(pane_id, p) for p in doomed],
            lambda: self._do_close_action(
                lambda: self._layout.close_others(pane_id, anchor), pane_id, doomed
            ),
        )

    def _close_to_right(self, pane_id: str, anchor: Path) -> None:
        files = list(self._layout.pane(pane_id).open_files)
        if anchor not in files:
            return
        idx = files.index(anchor)
        doomed = files[idx + 1 :]
        self._guarded_close(
            [(pane_id, p) for p in doomed],
            lambda: self._do_close_action(
                lambda: self._layout.close_to_right(pane_id, anchor), pane_id, doomed
            ),
        )

    def _close_to_left(self, pane_id: str, anchor: Path) -> None:
        files = list(self._layout.pane(pane_id).open_files)
        if anchor not in files:
            return
        idx = files.index(anchor)
        doomed = files[:idx]
        self._guarded_close(
            [(pane_id, p) for p in doomed],
            lambda: self._do_close_action(
                lambda: self._layout.close_to_left(pane_id, anchor), pane_id, doomed
            ),
        )

    def _close_all(self, pane_id: str) -> None:
        doomed = list(self._layout.pane(pane_id).open_files)
        self._guarded_close(
            [(pane_id, p) for p in doomed],
            lambda: self._do_close_action(
                lambda: self._layout.close_all(pane_id), pane_id, doomed
            ),
        )

    def _close_saved(self, pane_id: str) -> None:
        # Close Saved by definition only closes clean tabs → never any
        # dirty in scope → no modal.
        self._layout.close_saved(
            pane_id, is_dirty=self._registry.is_dirty
        )
        # Best-effort unsubscribe: remove this pane from every buffer
        # subscriber set; idempotent for buffers that survive.
        for path in list(self._panes_dict().keys()):
            self._registry.unsubscribe(path, pane_id)
        self._persist()
        self._render()

    def _handle_drop(self, target_pane_id: str, args: Any) -> None:
        """Server-side drop handler.  `args` is the dict emitted by the
        JS drop handler attached in `_render_pane` — NiceGUI may wrap a
        single-arg emit() in a one-element list."""
        if isinstance(args, list) and len(args) == 1:
            args = args[0]
        if not isinstance(args, dict):
            return
        if target_pane_id not in self._panes_dict():
            return
        # File-tree → editor: just open the file in the target pane
        # (persistent — explicit drag is a stronger signal than a
        # single click, so no preview).  No split, no clone.
        if args.get("type") == "tree-row":
            source_path_str = args.get("source_path")
            if not source_path_str:
                return
            source_path = Path(source_path_str)
            before = source_path in self._layout.pane(
                target_pane_id
            ).open_files
            self._layout.open_file(
                target_pane_id, source_path, preview=False
            )
            if not before:
                self._registry.subscribe(source_path, target_pane_id)
            self._persist()
            self._render()
            return
        source_pane = args.get("source_pane")
        source_path_str = args.get("source_path")
        zone = args.get("zone")
        clone = bool(args.get("ctrl", False))
        if not (source_pane and source_path_str and zone):
            return
        if source_pane not in self._panes_dict():
            return
        source_path = Path(source_path_str)

        if zone == "center":
            self._drop_at_center(target_pane_id, source_pane, source_path, clone)
        elif zone in ("left", "right", "top", "bottom"):
            self._drop_at_edge(target_pane_id, source_pane, source_path, zone, clone)
        self._persist()
        self._render()

    def _drop_at_center(
        self,
        target_pid: str,
        source_pid: str,
        path: Path,
        clone: bool,
    ) -> None:
        if target_pid == source_pid:
            # Drop on own pane → no-op (or focus the tab; layout's
            # open_file is idempotent for same-pane + same-path).
            self._layout.open_file(target_pid, path)
            return
        # Move the file out of source first when not cloning.
        if not clone:
            self._layout.close_tab(source_pid, path)
            self._registry.unsubscribe(path, source_pid)
        # Add to target if not already there, focus regardless.
        before = path in self._layout.pane(target_pid).open_files
        self._layout.open_file(target_pid, path)
        if not before:
            self._registry.subscribe(path, target_pid)

    def _drop_at_edge(
        self,
        target_pid: str,
        source_pid: str,
        path: Path,
        side: str,
        clone: bool,
    ) -> None:
        # Same-pane edge drop where `path` is the pane's only tab:
        # moving it out empties the pane, which would auto-collapse —
        # and then the split has no anchor.  Treat as no-op.
        if source_pid == target_pid and not clone:
            src_files = self._layout.pane(source_pid).open_files
            if len(src_files) == 1 and src_files[0] == path:
                return
        # Always use clone-style split (ctrl=True) so layout.split
        # doesn't touch the source pane; we manage source-side state
        # here for both move and clone cases.
        if not clone and source_pid != target_pid:
            self._layout.close_tab(source_pid, path)
            self._registry.unsubscribe(path, source_pid)
        if not clone and source_pid == target_pid:
            # Same-pane move: use split's built-in close_tab.
            new_pid = self._layout.split(
                source_pid, side=side, file=path, ctrl=False  # type: ignore[arg-type]
            )
            self._registry.unsubscribe(path, source_pid)
            self._registry.subscribe(path, new_pid)
            return
        new_pid = self._layout.split(
            target_pid, side=side, file=path, ctrl=True  # type: ignore[arg-type]
        )
        self._registry.subscribe(path, new_pid)

    def _do_close_tab(self, pane_id: str, path: Path) -> None:
        self._layout.close_tab(pane_id, path)
        self._registry.unsubscribe(path, pane_id)
        self._persist()
        self._render()

    def _do_close_action(
        self,
        action: Callable[[], None],
        pane_id: str,
        doomed: list[Path],
    ) -> None:
        action()
        for path in doomed:
            self._registry.unsubscribe(path, pane_id)
        self._persist()
        self._render()

    def _guarded_close(
        self,
        affected: list[tuple[str, Path]],
        proceed: Callable[[], None],
    ) -> None:
        """If any of `affected` (pane_id, path) pairs would orphan a
        dirty buffer (i.e. last subscriber, and dirty), show a single
        confirm dialog before running `proceed`.  Otherwise run
        immediately."""
        will_lose: list[Path] = []
        seen: set[Path] = set()
        for pid, path in affected:
            if path in seen:
                continue
            seen.add(path)
            subs = self._registry.subscribers(path)
            remaining = subs - {pid}
            if not remaining and self._registry.is_dirty(path):
                will_lose.append(path)
        if not will_lose:
            proceed()
            return

        # Modal: one dialog summarising all dirty losses.  Save All
        # writes each to disk first, Don't Save discards, Cancel aborts.
        dialog = ui.dialog()
        with dialog, ui.card().classes("min-w-80"):
            ui.label("Save changes?").classes(
                "text-base font-semibold mb-2"
            )
            with ui.column().classes("text-sm text-slate-700 mb-3 gap-1"):
                for p in will_lose:
                    rel = (
                        p.relative_to(self._workspace)
                        if self._workspace in p.parents
                        else p
                    )
                    ui.label(f"• {rel}")
            with ui.row().classes("w-full justify-end gap-2"):
                def _cancel() -> None:
                    dialog.close()

                def _discard() -> None:
                    dialog.close()
                    proceed()

                def _save_all() -> None:
                    for path in will_lose:
                        try:
                            self._registry.save(path)
                        except OSError as exc:
                            ui.notify(
                                f"save failed for {path}: {exc}",
                                type="negative",
                            )
                            return
                    dialog.close()
                    proceed()

                ui.button("Cancel", on_click=_cancel).props(
                    "flat no-caps color=grey-7"
                )
                ui.button("Don't Save", on_click=_discard).props(
                    "flat no-caps color=warning"
                )
                ui.button("Save All", on_click=_save_all).props(
                    "unelevated no-caps color=primary"
                )
        dialog.open()

    def _save(self, pane_id: str, path: Path) -> None:
        try:
            self._registry.save(path)
        except OSError as exc:
            ui.notify(f"save failed: {exc}", type="negative")
            return
        ui.notify(
            f"saved {path.relative_to(self._workspace)}", type="positive"
        )
        # Only the dirty class needs to flip; avoid a full re-render
        # to preserve codemirror state.
        self._refresh_dirty(path)

    def _on_codemirror_change(
        self, pane_id: str, path: Path, args: Any
    ) -> None:
        # NiceGUI's update:model-value fires with the new value as
        # `args` (a single string for ui.codemirror).  Push into the
        # buffer; broadcast is handled by BufferRegistry.on_change.
        new_text = args if isinstance(args, str) else ""
        self._registry.set_text(path, new_text)

    def _on_cm_change(self, path: Path, new_value: str) -> None:
        """Forward a codemirror text change to the buffer registry.

        Two guards keep stale / spurious change events from poisoning
        the buffer:

        1. `_rendering` gate — during a `_render()` cycle, codemirror's
           old / new Vue instances briefly coexist and the JS-side
           `update:value` channel can fire with intermediate state
           (empty string from the empty-change-set decode path, etc.).
           These all show up as "edits" the user never made and
           would otherwise mark the buffer dirty.
        2. Empty-buffer artefact — even outside `_render`, an
           `update:value` carrying `""` when our buffer holds real
           content is almost certainly a transition echo, not a user
           clearing the doc.
        """
        if self._rendering:
            return
        if new_value == "" and self._registry.text(path) != "":
            return
        # A real edit on a previewed tab promotes it — the tab stops
        # being replaced by the next single-click in the file tree.
        active_pid = self._layout.active_pane_id
        if active_pid in self._panes_dict():
            pv = self._layout.pane(active_pid)
            if pv.preview_file == path:
                self._layout.make_persistent(active_pid, path)
                tab = self._pane_widgets.get(active_pid, {}).get(
                    "tabs", {}
                ).get(path)
                if tab is not None:
                    tab.classes(remove="preview")
        self._registry.set_text(path, new_value)

    def _on_buffer_change(self, path: Path) -> None:
        """Called by BufferRegistry whenever any pane edits `path`.
        Re-syncs subscribers' codemirror values, refreshes their tab
        dirty class, and re-renders any preview-mode panes currently
        showing `path` so the read-only view tracks live edits."""
        new_text = self._registry.text(path)
        for pid, widgets in self._pane_widgets.items():
            pane = self._layout.pane(pid)
            if pane.active_file != path:
                continue
            cm = widgets.get("codemirror")
            if cm is not None and cm.value != new_text:
                cm.value = new_text
            if self._pane_modes.get(pid) == "preview":
                preview_box = widgets.get("preview_box")
                if preview_box is not None:
                    preview_box.clear()
                    with preview_box:
                        ui.html(
                            render_for_path(path, new_text), sanitize=False
                        )
        self._refresh_dirty(path)

    # ─── persistence ─────────────────────────────────────────────────

    def _layout_path(self) -> Path:
        return self._workspace / _LAYOUT_FILE

    def _load_or_init_layout(self) -> EditorLayout:
        path = self._layout_path()
        if path.exists():
            try:
                blob = json.loads(path.read_text(encoding="utf-8"))
                return EditorLayout.from_dict(
                    blob, file_exists=lambda p: Path(p).exists()
                )
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning(
                    "could not restore layout from %s: %s — falling back "
                    "to fresh layout",
                    path,
                    exc,
                )
        layout = EditorLayout()
        case_md = self._workspace / "CASE.md"
        if case_md.exists():
            layout.open_file(layout.active_pane_id, case_md)
        return layout

    def _persist(self) -> None:
        try:
            self._layout_path().write_text(
                json.dumps(self._layout.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("could not persist layout: %s", exc)

    # ─── disk I/O (injected into BufferRegistry) ─────────────────────

    @staticmethod
    def _read_disk(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            return f"(unreadable: {exc.__class__.__name__}: {exc})"

    @staticmethod
    def _write_disk(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    # ─── small helpers ───────────────────────────────────────────────

    def _all_pane_ids(self) -> list[str]:
        return list(self._panes_dict().keys())

    def _panes_dict(self) -> dict[str, Any]:
        # Access EditorLayout's internal pane map — we don't expose a
        # public iterator on EditorLayout (the tree itself is the
        # public surface).  This is fine for the view since the view
        # and the model live in the same package.
        return self._layout._panes  # type: ignore[attr-defined]
