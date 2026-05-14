"""Left-sidebar file tree (Explorer) for the case page.

VSCode-style explorer with full file operations:

- single-click → preview-open in active pane (italic tab)
- double-click → persistent open
- Ctrl/Shift multi-select with anchor
- F2 / right-click → inline rename (red border on conflict)
- Delete / right-click → delete (asks once for dirty buffers)
- Ctrl+X / Ctrl+C / Ctrl+V → cut / copy / paste
- drag-drop within tree → move (rename on disk)
- drag-drop tree → editor pane → open file in that pane
- header buttons → +File, +Folder, refresh, collapse-all
- expansion state persisted to `<workspace>/.tree-state.json`

The tree owns no editor / buffer state — it dispatches `on_open` for
preview/persistent opens, and calls `on_buffer_path_changed(old, new)`
after a rename / move so the editor can patch any open tabs.
"""

from __future__ import annotations

import json
import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from nicegui import ui

from rca_ui.ui._drag_payload import parse_drop_payload

logger = logging.getLogger(__name__)

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

# Bookkeeping files we own — must not be deleted / renamed by the user
# and stay hidden from view.
_BOOKKEEPING_NAMES = frozenset({".editor-layout.json", ".tree-state.json"})

_TREE_STATE_FILE = ".tree-state.json"


def _icon_for(p: Path) -> str:
    suf = p.suffix.lower()
    if suf in (".json", ".jsonl"):
        return "data_object"
    if suf == ".py":
        return "code"
    if suf in (".md", ".markdown"):
        return "article"
    return "insert_drive_file"


def _is_hidden(path: Path) -> bool:
    if path.name in _HIDDEN_PARTS or path.name in _BOOKKEEPING_NAMES:
        return True
    # Dot-prefixed names other than the workspace itself stay hidden.
    return path.name.startswith(".") and path.name not in (".",)


def _parents_to_expand(workspace: Path, path: Path) -> list[Path]:
    """Resolved ancestor dirs of `path` between `workspace` (exclusive)
    and `path` (exclusive), in outer→inner order.

    Empty list when `path` is a direct child of `workspace` (nothing
    to open) or when `path` is not under `workspace` at all (reveal
    silently no-ops).  All returned paths are `.resolve()`d so they
    compare equal to the keys FileTree stores in its `_expanded`
    set."""
    try:
        rel = path.resolve().relative_to(workspace.resolve())
    except ValueError:
        return []
    parents: list[Path] = []
    cur = workspace
    for part in rel.parts[:-1]:
        cur = cur / part
        parents.append(cur.resolve())
    return parents


def _dir_entries(dir_path: Path) -> list[Path]:
    """Sorted children of `dir_path`: directories first
    (alphabetical), then files (priority names first, then
    alphabetical).  Hidden entries dropped."""
    children: list[Path] = []
    try:
        for child in dir_path.iterdir():
            if _is_hidden(child):
                continue
            children.append(child)
    except OSError:
        return []

    def _key(p: Path) -> tuple[int, int, str]:
        if p.is_dir():
            return (0, 0, p.name.lower())
        try:
            return (1, _PRIORITY_FILES.index(p.name), p.name.lower())
        except ValueError:
            return (1, len(_PRIORITY_FILES), p.name.lower())

    return sorted(children, key=_key)


@dataclass
class _InlineEdit:
    """Active inline edit (rename or create-new)."""

    mode: Literal["rename", "new-file", "new-folder"]
    # Parent dir the row will live in once committed.  For rename, this
    # is target.parent; for new-file/new-folder, this is the chosen
    # parent (selected dir, or parent-of-selected-file, or workspace).
    parent: Path
    # For rename: original path.  None for new-file / new-folder.
    original: Path | None = None
    # Pre-fill text in the input (filename for rename, "" for new).
    initial: str = ""


@dataclass
class _Clipboard:
    # Resolved absolute paths so membership checks against `_row_class`
    # don't need to re-resolve every row.  Order doesn't matter — paste
    # always pastes by name into the target dir.
    paths: set[Path] = field(default_factory=set)
    cut: bool = False


class FileTree:
    """Explorer panel.  Owns: selection, expansion, clipboard, inline
    edit, and disk operations.  Calls back to the editor for opens and
    for buffer-path renames after a successful disk move."""

    _INDENT_PX = 12  # per-depth left padding

    def __init__(
        self,
        *,
        workspace: Path,
        container: Any,
        on_open: Callable[[Path, bool], None],
        is_active: Callable[[Path], bool],
        is_dirty: Callable[[Path], bool] | None = None,
        on_buffer_path_changed: Callable[[Path, Path | None], None] | None = None,
    ) -> None:
        """
        `on_open(path, preview)` — single-click → preview=True,
                                   double-click → preview=False.
        `is_active(path)` — current editor's active file (for selection
                             highlight).
        `is_dirty(path)` — buffer dirty? Used by the delete-confirm
                            modal.
        `on_buffer_path_changed(old, new)` — after a rename/move on
                                              disk, the editor patches
                                              its open tabs.  `new=None`
                                              means the file is gone
                                              (use mark_deleted).
        """
        self._workspace = workspace
        self._container = container
        self._on_open = on_open
        self._is_active = is_active
        self._is_dirty = is_dirty or (lambda _p: False)
        self._on_buffer_path_changed = on_buffer_path_changed or (
            lambda _o, _n: None
        )

        self._expanded: set[Path] = set()
        self._initial_done = False
        # Display-order list of rendered row paths.  Repopulated each
        # `_render` from `_render_dir_contents`; used by keyboard nav
        # (`_move_cursor`) and range-select.
        self._rows: list[Path] = []
        # Selection / anchor / clipboard paths are stored in their
        # resolved-absolute form so membership tests are O(1) and
        # don't need to re-resolve every row in `_row_class`.  Callers
        # still pass un-resolved paths in via the public API — we
        # normalise on insert.
        self._selection: set[Path] = set()
        self._anchor: Path | None = None
        self._clipboard = _Clipboard()
        self._edit: _InlineEdit | None = None
        # Set during _render to suppress side-effects of the edit input
        # being mounted / focused.
        self._rendering = False

        self._load_tree_state()
        self._install_global_keyboard()

    # ─── public API ──────────────────────────────────────────────────

    def refresh(self) -> None:
        """Re-read disk, re-render the tree.  Called by the host after
        the agent's turn, after disk operations, etc."""
        self._render()

    def reveal(self, path: Path) -> None:
        """Expand every parent of `path` so the row becomes visible,
        sync the tree's anchor / selection to that path (so the row
        highlight follows the editor's active file), re-render, and
        scroll the row into view."""
        if path is None:
            return
        try:
            path.resolve().relative_to(self._workspace.resolve())
        except ValueError:
            return  # outside workspace — silently skip
        parents = _parents_to_expand(self._workspace, path)
        self._expanded.update(parents)
        # Anchor / selection follow the active file so .selected,
        # .selected-anchor never end up on different rows.
        resolved = path.resolve()
        self._selection = {resolved}
        self._anchor = resolved
        logger.info(
            "reveal(%s): parents added=%d, _expanded=%d entries",
            path, len(parents), len(self._expanded),
        )
        self._persist_tree_state()
        self._render()
        # `scrollIntoView` runs client-side on the matching DOM node.
        # We tag the row's element with a unique class via _render's
        # `data-tree-path` attribute lookup.  Non-critical — wrap in
        # try/except so a dead slot context doesn't abort reveal().
        try:
            ui.run_javascript(
                "(() => {"
                f' const el = document.querySelector('
                f'  \'[data-tree-path={json.dumps(str(path))}]\''
                ");"
                ' if (el) el.scrollIntoView({block: "nearest"});'
                "})()"
            )
        except RuntimeError:
            logger.debug("scrollIntoView skipped — slot context unavailable")

    # ─── render ──────────────────────────────────────────────────────

    def _render(self) -> None:
        if not self._initial_done:
            # First refresh seeds the top-level dirs as expanded so the
            # user sees their immediate contents.
            for child in _dir_entries(self._workspace):
                if child.is_dir():
                    self._expanded.add(child.resolve())
            self._initial_done = True

        self._rendering = True
        self._container.clear()
        self._rows = []
        with self._container:
            # Header toolbar (4 buttons).  Render first so it stays
            # pinned visually even with a tall tree below it.
            self._render_header()
            # Drop target for "drop into workspace root".
            tree_body = ui.element("div").classes("rca-tree-body")
            self._wire_root_drop(tree_body)
            with tree_body:
                self._render_dir_contents(self._workspace, depth=0)
        self._rendering = False

    def _render_header(self) -> None:
        with ui.element("div").classes("rca-tree-header"):
            new_file = (
                ui.element("div")
                .classes("rca-tree-btn")
                .tooltip("New File")
            )
            with new_file:
                ui.icon("note_add").style("font-size:16px;")
            new_file.on("click", lambda _e: self._begin_new_file(None))

            new_folder = (
                ui.element("div")
                .classes("rca-tree-btn")
                .tooltip("New Folder")
            )
            with new_folder:
                ui.icon("create_new_folder").style("font-size:16px;")
            new_folder.on("click", lambda _e: self._begin_new_folder(None))

            refresh_btn = (
                ui.element("div").classes("rca-tree-btn").tooltip("Refresh")
            )
            with refresh_btn:
                ui.icon("refresh").style("font-size:16px;")
            refresh_btn.on("click", lambda _e: self._render())

            collapse_btn = (
                ui.element("div")
                .classes("rca-tree-btn")
                .tooltip("Collapse All")
            )
            with collapse_btn:
                ui.icon("unfold_less").style("font-size:16px;")
            collapse_btn.on("click", lambda _e: self._collapse_all())

    def _render_dir_contents(self, dir_path: Path, depth: int) -> None:
        # When an inline-create edit is rooted at this directory and
        # we're editing, render the input at the top of the dir.
        if (
            self._edit is not None
            and self._edit.mode in ("new-file", "new-folder")
            and self._edit.parent.resolve() == dir_path.resolve()
        ):
            self._render_inline_create_row(depth)

        for entry in _dir_entries(dir_path):
            if entry.is_dir():
                expanded = entry.resolve() in self._expanded
                self._render_dir_row(entry, depth, expanded)
                if expanded:
                    self._render_dir_contents(entry, depth + 1)
            else:
                self._render_file_row(entry, depth)

    def _render_dir_row(
        self, path: Path, depth: int, expanded: bool
    ) -> None:
        # If a rename edit targets this dir, render the rename input
        # instead of the row.
        if (
            self._edit is not None
            and self._edit.mode == "rename"
            and self._edit.original is not None
            and self._edit.original.resolve() == path.resolve()
        ):
            self._render_rename_row(depth, is_dir=True)
            return

        row_el = ui.element("div").classes(self._row_class(path, is_dir=True))
        row_el.props(f"data-tree-path={json.dumps(str(path))}")
        with row_el:
            self._indent(depth)
            with ui.element("div").classes("chevron"):
                ui.icon("expand_more" if expanded else "chevron_right")
            with ui.element("div").classes("row-icon-slot"):
                ui.icon(
                    "folder_open" if expanded else "folder"
                ).classes("row-icon")
            ui.label(path.name).classes("name")
            self._attach_context_menu(path, is_dir=True)
        self._wire_row_events(row_el, path, is_dir=True)
        self._rows.append(path)

    def _render_file_row(self, path: Path, depth: int) -> None:
        if (
            self._edit is not None
            and self._edit.mode == "rename"
            and self._edit.original is not None
            and self._edit.original.resolve() == path.resolve()
        ):
            self._render_rename_row(depth, is_dir=False)
            return

        row_el = ui.element("div").classes(self._row_class(path, is_dir=False))
        row_el.props(f"data-tree-path={json.dumps(str(path))}")
        with row_el:
            self._indent(depth)
            ui.element("div").classes("chevron")
            with ui.element("div").classes("row-icon-slot"):
                ui.icon(_icon_for(path)).classes("row-icon")
            ui.label(path.name).classes("name")
            self._attach_context_menu(path, is_dir=False)
        self._wire_row_events(row_el, path, is_dir=False)
        self._rows.append(path)

    def _row_class(self, path: Path, *, is_dir: bool) -> str:
        # `_selection`, `_anchor`, and `_clipboard.paths` all store
        # resolved paths so the per-row check is one resolve() + a
        # set lookup — no O(N²) comprehension across every row.
        resolved = path.resolve()
        cls = ["rca-file-row"]
        if is_dir:
            cls.append("rca-dir-row")
        if resolved in self._selection:
            cls.append("selected-multi")
        if self._anchor is not None and self._anchor == resolved:
            cls.append("selected-anchor")
        if not is_dir and self._is_active(path):
            cls.append("selected")
        if self._clipboard.cut and resolved in self._clipboard.paths:
            cls.append("cut")
        return " ".join(cls)

    def _indent(self, depth: int) -> None:
        if depth <= 0:
            return
        ui.element("div").style(
            f"width:{depth * self._INDENT_PX}px;flex-shrink:0;"
        )

    # ─── inline-edit input rendering ────────────────────────────────

    def _render_rename_row(self, depth: int, *, is_dir: bool) -> None:
        assert self._edit is not None
        edit = self._edit
        row = ui.element("div").classes("rca-file-row rca-inline-edit-row")
        with row:
            self._indent(depth)
            ui.element("div").classes("chevron")
            with ui.element("div").classes("row-icon-slot"):
                icon_name = (
                    "folder" if is_dir
                    else _icon_for(Path(edit.initial or "x"))
                )
                ui.icon(icon_name).classes("row-icon")
            self._mount_inline_input(edit)

    def _render_inline_create_row(self, depth: int) -> None:
        assert self._edit is not None
        edit = self._edit
        row = ui.element("div").classes("rca-file-row rca-inline-edit-row")
        with row:
            self._indent(depth)
            ui.element("div").classes("chevron")
            with ui.element("div").classes("row-icon-slot"):
                icon_name = (
                    "folder" if edit.mode == "new-folder" else "insert_drive_file"
                )
                ui.icon(icon_name).classes("row-icon")
            self._mount_inline_input(edit)

    def _mount_inline_input(self, edit: _InlineEdit) -> None:
        # ui.input has autofocus + blur/keydown wired to our commit /
        # cancel helpers.  The red-border conflict check runs client-
        # side via Vue binding to a Python on_change handler.
        inp = ui.input(value=edit.initial).props(
            "outlined dense autofocus borderless"
        ).classes("rca-inline-input")
        inp.on(
            "keydown.enter",
            lambda _e: self._commit_inline_edit(inp.value or ""),
        )
        inp.on(
            "keydown.escape",
            lambda _e: self._cancel_inline_edit(),
        )
        inp.on("blur", lambda _e: self._commit_inline_edit(inp.value or ""))

        def _validate(_e: Any) -> None:
            name = (inp.value or "").strip()
            if not name:
                inp.classes(remove="rca-inline-conflict")
                return
            candidate = edit.parent / name
            conflict = (
                candidate.exists()
                and (
                    edit.mode != "rename"
                    or edit.original is None
                    or candidate.resolve() != edit.original.resolve()
                )
            )
            if conflict:
                inp.classes(add="rca-inline-conflict")
            else:
                inp.classes(remove="rca-inline-conflict")

        inp.on("update:model-value", _validate)
        # Select stem (everything before the dot) for renames so a
        # typical "rename without changing extension" is one keystroke.
        if edit.mode == "rename":
            ui.run_javascript(
                "setTimeout(() => {"
                ' const el = document.querySelector(".rca-inline-input input");'
                " if (!el) return;"
                " el.focus();"
                ' const v = el.value || "";'
                ' const dot = v.lastIndexOf(".");'
                " const end = dot > 0 ? dot : v.length;"
                " el.setSelectionRange(0, end);"
                "}, 50);"
            )

    # ─── event wiring per row ────────────────────────────────────────

    def _wire_row_events(self, row_el: Any, path: Path, *, is_dir: bool) -> None:
        # Single-click & double-click are distinct DOM events; we use
        # NiceGUI modifiers on click to read shift/ctrl.
        row_el.on(
            "click",
            lambda e, p=path, d=is_dir: self._on_row_click(p, d, e),
        )
        row_el.on(
            "dblclick",
            lambda _e, p=path, d=is_dir: self._on_row_dblclick(p, d),
        )
        # Drag source — pack a JSON payload with type='tree-row'.
        row_el.props("draggable=true")
        row_el.on(
            "dragstart",
            None,
            js_handler=(
                "(event) => {"
                # If the dragged row isn't part of the current selection,
                # selection-as-drag-payload is the surprise-free choice.
                # Otherwise drag the whole selection (multi-file move).
                # The Python side reads `paths` to support multi-drag.
                f' const path = {json.dumps(str(path))};'
                # Marker class on the drag image — visual feedback only.
                ' event.dataTransfer.setData("text/plain", JSON.stringify({'
                '  type: "tree-row",'
                "  path: path,"
                "  paths: [path]"
                " }));"
                ' event.dataTransfer.effectAllowed = "copyMove";'
                "}"
            ),
        )
        # Tree row also accepts drops (for in-tree move).  Drop target
        # rules: drop onto a dir → move into dir; drop onto a file →
        # move into its parent.
        row_el.on(
            "dragover",
            None,
            js_handler=(
                "(event) => {"
                " event.preventDefault();"
                ' event.dataTransfer.dropEffect = "move";'
                ' event.currentTarget.classList.add("drag-over");'
                "}"
            ),
        )
        row_el.on(
            "dragleave",
            None,
            js_handler=(
                "(event) => {"
                ' event.currentTarget.classList.remove("drag-over");'
                "}"
            ),
        )
        row_el.on(
            "drop",
            lambda e, p=path, d=is_dir: self._handle_tree_drop(p, d, e.args),
            js_handler=(
                "(event) => {"
                " event.preventDefault();"
                " event.stopPropagation();"
                ' event.currentTarget.classList.remove("drag-over");'
                ' const dt = event.dataTransfer.getData("text/plain");'
                " if (!dt) return;"
                " try { emit(JSON.parse(dt)); }"
                " catch (_e) { return; }"
                "}"
            ),
        )

    def _wire_root_drop(self, body_el: Any) -> None:
        """Drops on the empty tree area go to the workspace root."""
        body_el.on(
            "dragover",
            None,
            js_handler=(
                "(event) => {"
                " event.preventDefault();"
                ' event.dataTransfer.dropEffect = "move";'
                "}"
            ),
        )
        body_el.on(
            "drop",
            lambda e: self._handle_tree_drop(
                self._workspace, True, e.args
            ),
            js_handler=(
                "(event) => {"
                " event.preventDefault();"
                ' const dt = event.dataTransfer.getData("text/plain");'
                " if (!dt) return;"
                " try { emit(JSON.parse(dt)); }"
                " catch (_e) { return; }"
                "}"
            ),
        )

    # ─── click handlers ──────────────────────────────────────────────

    def _on_row_click(
        self, path: Path, is_dir: bool, e: Any
    ) -> None:
        if self._edit is not None:
            return
        mods = getattr(e, "modifiers", None)
        ctrl = bool(mods and (mods.ctrl or mods.meta))
        shift = bool(mods and mods.shift)
        if ctrl:
            self._toggle_select(path)
            return
        if shift and self._anchor is not None:
            self._range_select(self._anchor, path)
            return
        # Plain click — single-select + activation.
        self._select_only(path)
        if is_dir:
            self._toggle_expand(path)
        else:
            # Preview-open (italic tab).
            self._on_open(path, True)

    def _on_row_dblclick(self, path: Path, is_dir: bool) -> None:
        if self._edit is not None:
            return
        if is_dir:
            # Dirs don't have a "promote" concept — leave toggle to
            # the single click.
            return
        # Persistent open (non-italic tab).
        self._on_open(path, False)

    def _select_only(self, path: Path) -> None:
        resolved = path.resolve()
        self._selection = {resolved}
        self._anchor = resolved
        self._render()

    def _toggle_select(self, path: Path) -> None:
        resolved = path.resolve()
        if resolved in self._selection:
            self._selection.discard(resolved)
        else:
            self._selection.add(resolved)
        self._anchor = resolved
        self._render()

    def _range_select(self, anchor: Path, target: Path) -> None:
        # Range over the currently-rendered row list (display order).
        # Anchor / target may be either un-resolved (from click args)
        # or resolved (from internal state) — normalise on compare.
        paths = list(self._rows)
        anchor_res = anchor.resolve()
        target_res = target.resolve()
        try:
            a = next(
                i for i, p in enumerate(paths) if p.resolve() == anchor_res
            )
            b = next(
                i for i, p in enumerate(paths) if p.resolve() == target_res
            )
        except StopIteration:
            self._select_only(target)
            return
        lo, hi = sorted((a, b))
        self._selection = {p.resolve() for p in paths[lo : hi + 1]}
        self._render()

    def _toggle_expand(self, path: Path) -> None:
        key = path.resolve()
        if key in self._expanded:
            self._expanded.discard(key)
        else:
            self._expanded.add(key)
        self._persist_tree_state()
        self._render()

    def _collapse_all(self) -> None:
        self._expanded.clear()
        self._persist_tree_state()
        self._render()

    # ─── context menu ────────────────────────────────────────────────

    def _attach_context_menu(self, path: Path, *, is_dir: bool) -> None:
        with ui.context_menu():
            ui.menu_item(
                "New File",
                lambda _e=None, p=path, d=is_dir: self._begin_new_file(
                    p if d else p.parent
                ),
            )
            ui.menu_item(
                "New Folder",
                lambda _e=None, p=path, d=is_dir: self._begin_new_folder(
                    p if d else p.parent
                ),
            )
            ui.separator()
            ui.menu_item(
                "Rename  (F2)",
                lambda _e=None, p=path: self._begin_rename(p),
            )
            ui.menu_item(
                "Delete  (Del)",
                lambda _e=None, p=path: self._delete_paths([p]),
            )
            ui.separator()
            ui.menu_item(
                "Cut  (Ctrl+X)",
                lambda _e=None: self._cut_selection_or(path),
            )
            ui.menu_item(
                "Copy  (Ctrl+C)",
                lambda _e=None: self._copy_selection_or(path),
            )
            ui.menu_item(
                "Paste  (Ctrl+V)",
                lambda _e=None, p=path, d=is_dir: self._paste_into(
                    p if d else p.parent
                ),
            )
            ui.separator()
            ui.menu_item("Refresh", lambda _e=None: self._render())

    # ─── inline-edit lifecycle ──────────────────────────────────────

    def _begin_rename(self, path: Path) -> None:
        self._edit = _InlineEdit(
            mode="rename",
            parent=path.parent,
            original=path,
            initial=path.name,
        )
        self._render()

    def _begin_new_file(self, parent: Path | None) -> None:
        target_parent = self._resolve_create_parent(parent)
        # Ensure the parent dir is expanded so the input is visible.
        self._expanded.add(target_parent.resolve())
        self._edit = _InlineEdit(
            mode="new-file", parent=target_parent, initial=""
        )
        self._render()

    def _begin_new_folder(self, parent: Path | None) -> None:
        target_parent = self._resolve_create_parent(parent)
        self._expanded.add(target_parent.resolve())
        self._edit = _InlineEdit(
            mode="new-folder", parent=target_parent, initial=""
        )
        self._render()

    def _resolve_create_parent(self, parent: Path | None) -> Path:
        """If `parent` is supplied use it; otherwise derive from the
        current selection (anchor's dir, or anchor itself if dir,
        falling back to workspace root)."""
        if parent is not None and parent.is_dir():
            return parent
        if self._anchor is not None and self._anchor.exists():
            return (
                self._anchor if self._anchor.is_dir() else self._anchor.parent
            )
        return self._workspace

    def _commit_inline_edit(self, raw_name: str) -> None:
        if self._edit is None or self._rendering:
            return
        edit = self._edit
        name = raw_name.strip()
        if not name:
            self._cancel_inline_edit()
            return
        candidate = edit.parent / name
        # Conflict check — for rename, allow if it's the same path.
        same_as_original = (
            edit.mode == "rename"
            and edit.original is not None
            and candidate.resolve() == edit.original.resolve()
        )
        if candidate.exists() and not same_as_original:
            ui.notify(
                f"{candidate.name} already exists in {edit.parent.name}",
                type="warning",
            )
            return
        # Clear edit state BEFORE the disk op so re-renders triggered
        # by callbacks don't try to draw a stale input.
        self._edit = None
        try:
            if edit.mode == "rename" and edit.original is not None:
                if same_as_original:
                    self._render()
                    return
                edit.original.rename(candidate)
                self._on_buffer_path_changed(edit.original, candidate)
                # Update any expanded dir key referring to the old path.
                if edit.original.resolve() in self._expanded:
                    self._expanded.discard(edit.original.resolve())
                    self._expanded.add(candidate.resolve())
                resolved = candidate.resolve()
                self._selection = {resolved}
                self._anchor = resolved
            elif edit.mode == "new-file":
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.touch()
                resolved = candidate.resolve()
                self._selection = {resolved}
                self._anchor = resolved
                # Auto-open new file persistently.
                self._on_open(candidate, False)
            elif edit.mode == "new-folder":
                candidate.mkdir(parents=True, exist_ok=False)
                resolved = candidate.resolve()
                self._expanded.add(resolved)
                self._selection = {resolved}
                self._anchor = resolved
        except OSError as exc:
            ui.notify(f"failed: {exc}", type="negative")
        self._persist_tree_state()
        self._render()

    def _cancel_inline_edit(self) -> None:
        if self._edit is None:
            return
        self._edit = None
        self._render()

    # ─── delete / cut / copy / paste ────────────────────────────────

    def _delete_paths(self, paths: list[Path]) -> None:
        if not paths:
            return
        # Filter out bookkeeping accidentally selected.
        paths = [p for p in paths if p.name not in _BOOKKEEPING_NAMES]
        if not paths:
            return
        # Identify dirty buffers that would be orphaned.  We can't
        # introspect the editor here, so trust `is_dirty` per path
        # (the editor wires this in via `is_dirty` constructor arg).
        descendants: list[Path] = []
        for p in paths:
            if p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file():
                        descendants.append(sub)
            else:
                descendants.append(p)
        dirty = [d for d in descendants if self._is_dirty(d)]

        def _do_delete() -> None:
            for p in paths:
                try:
                    if p.is_dir():
                        # Notify editor for every open file descendant so
                        # their tabs flip to strike-through.
                        for sub in p.rglob("*"):
                            if sub.is_file():
                                self._on_buffer_path_changed(sub, None)
                        shutil.rmtree(p)
                    else:
                        self._on_buffer_path_changed(p, None)
                        p.unlink()
                except OSError as exc:
                    ui.notify(f"delete failed: {exc}", type="negative")
            # Clear selection / clipboard entries for deleted paths.
            self._selection = {s for s in self._selection if s.exists()}
            self._clipboard.paths = {
                p for p in self._clipboard.paths if p.exists()
            }
            self._render()

        if dirty:
            self._confirm_delete(paths, dirty, _do_delete)
        else:
            _do_delete()

    def _confirm_delete(
        self, paths: list[Path], dirty: list[Path], proceed: Callable[[], None]
    ) -> None:
        dialog = ui.dialog()
        with dialog, ui.card().classes("min-w-80"):
            ui.label("Delete with unsaved changes?").classes(
                "text-base font-semibold mb-2"
            )
            with ui.column().classes("text-sm text-slate-700 mb-3 gap-1"):
                ui.label(
                    f"{len(paths)} item(s) — {len(dirty)} have unsaved edits."
                )
                ui.label(
                    "Deleting will leave the open tab(s) as "
                    "strike-through orphans; Save will recreate them."
                ).classes("text-xs text-slate-500")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel", on_click=lambda: dialog.close()
                ).props("flat no-caps color=grey-7")

                def _go() -> None:
                    dialog.close()
                    proceed()

                ui.button(
                    "Delete", on_click=_go
                ).props("unelevated no-caps color=negative")
        dialog.open()

    def _cut_selection_or(self, fallback: Path) -> None:
        paths = (
            set(self._selection) if self._selection else {fallback.resolve()}
        )
        self._clipboard = _Clipboard(paths=paths, cut=True)
        self._render()

    def _copy_selection_or(self, fallback: Path) -> None:
        paths = (
            set(self._selection) if self._selection else {fallback.resolve()}
        )
        self._clipboard = _Clipboard(paths=paths, cut=False)
        self._render()

    def _paste_into(self, target_dir: Path) -> None:
        if not self._clipboard.paths:
            return
        if not target_dir.is_dir():
            target_dir = target_dir.parent
        for src in list(self._clipboard.paths):
            if not src.exists():
                continue
            # Refuse to paste a dir into itself or a descendant.
            try:
                target_dir.resolve().relative_to(src.resolve())
                if src.is_dir():
                    ui.notify(
                        f"can't paste {src.name} into itself",
                        type="warning",
                    )
                    continue
            except ValueError:
                pass
            dest = target_dir / src.name
            try:
                if dest.exists():
                    # Overwrite: remove dest then move/copy.  Notify the
                    # editor so any open tab for `dest` becomes
                    # deleted-dirty.
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        self._on_buffer_path_changed(dest, None)
                        dest.unlink()
                if self._clipboard.cut:
                    src.rename(dest)
                    self._on_buffer_path_changed(src, dest)
                else:
                    if src.is_dir():
                        shutil.copytree(src, dest)
                    else:
                        shutil.copy2(src, dest)
            except OSError as exc:
                ui.notify(f"paste failed: {exc}", type="negative")
                continue
        # Cut clears clipboard, copy persists it.
        if self._clipboard.cut:
            self._clipboard = _Clipboard()
        self._render()

    # ─── tree drag-drop (moves on disk) ─────────────────────────────

    def _handle_tree_drop(
        self, target: Path, target_is_dir: bool, args: Any
    ) -> None:
        payload = parse_drop_payload(args)
        if payload is None or payload.kind != "tree-row":
            # tab-into-tree isn't a supported use case yet.
            return
        sources = [p for p in payload.source_paths if p.exists()]
        if not sources:
            return
        target_dir = target if target_is_dir else target.parent
        for src in sources:
            if not src.exists():
                continue
            # No-op if dropping onto own parent.
            if src.parent.resolve() == target_dir.resolve():
                continue
            # No moving a dir into itself / a descendant.
            try:
                target_dir.resolve().relative_to(src.resolve())
                ui.notify(
                    f"can't move {src.name} into itself", type="warning"
                )
                continue
            except ValueError:
                pass
            dest = target_dir / src.name
            try:
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        self._on_buffer_path_changed(dest, None)
                        dest.unlink()
                src.rename(dest)
                self._on_buffer_path_changed(src, dest)
                if src.resolve() in self._expanded:
                    self._expanded.discard(src.resolve())
                    self._expanded.add(dest.resolve())
            except OSError as exc:
                ui.notify(f"move failed: {exc}", type="negative")
        self._persist_tree_state()
        self._render()

    # ─── keyboard ───────────────────────────────────────────────────

    def _install_global_keyboard(self) -> None:
        # Use NiceGUI's default `ignore` list — Ctrl+X / Ctrl+C /
        # arrows etc. fire only when the focus is NOT in a text
        # editor (codemirror, ui.input, ui.textarea, ui.editor).
        # Passing `ignore=[]` would let the tree hijack copy/paste
        # while the user is editing code or typing in chat.
        ui.keyboard(on_key=self._on_key, repeating=False)

    def _on_key(self, e: Any) -> None:
        if not e.action.keydown:
            return
        # Suppress all tree shortcuts while an inline edit is active —
        # the input itself handles Enter / Escape.
        if self._edit is not None:
            return
        code = e.key.code
        ctrl = bool(e.modifiers.ctrl or e.modifiers.meta)
        shift = bool(e.modifiers.shift)
        # The tree's keyboard shortcuts should only fire when the user
        # is interacting with the tree.  We use a coarse approximation:
        # any tree-row anchor exists.  Active codemirror eats most keys
        # before we see them because NiceGUI binds at the document
        # level — Ctrl+C inside a codemirror is consumed by the editor.
        if code == "F2" and self._anchor is not None:
            self._begin_rename(self._anchor)
        elif code == "Delete" and self._selection:
            self._delete_paths(list(self._selection))
        elif code == "Escape":
            if self._clipboard.paths:
                self._clipboard = _Clipboard()
                self._render()
        elif ctrl and code == "KeyX" and self._selection:
            self._cut_selection_or(next(iter(self._selection)))
        elif ctrl and code == "KeyC" and self._selection:
            self._copy_selection_or(next(iter(self._selection)))
        elif ctrl and code == "KeyV":
            target = self._anchor or self._workspace
            self._paste_into(target if target.is_dir() else target.parent)
        elif code == "ArrowDown":
            self._move_cursor(+1, shift=shift)
        elif code == "ArrowUp":
            self._move_cursor(-1, shift=shift)
        elif code == "Enter" and self._anchor is not None:
            if self._anchor.is_dir():
                self._toggle_expand(self._anchor)
            else:
                self._on_open(self._anchor, False)

    def _move_cursor(self, delta: int, *, shift: bool) -> None:
        if not self._rows:
            return
        if self._anchor is None:
            self._anchor = self._rows[0].resolve()
            self._selection = {self._anchor}
            self._render()
            return
        idx = next(
            (
                i for i, p in enumerate(self._rows)
                if p.resolve() == self._anchor
            ),
            None,
        )
        if idx is None:
            return
        new_idx = max(0, min(len(self._rows) - 1, idx + delta))
        new_path = self._rows[new_idx]
        if shift:
            self._range_select(self._anchor, new_path)
        else:
            self._select_only(new_path)

    # ─── persistence ────────────────────────────────────────────────

    def _state_path(self) -> Path:
        return self._workspace / _TREE_STATE_FILE

    def _load_tree_state(self) -> None:
        path = self._state_path()
        if not path.exists():
            return
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("could not read tree state: %s", exc)
            return
        for s in blob.get("expanded", []):
            try:
                p = Path(s)
                if p.exists() and p.is_dir():
                    self._expanded.add(p.resolve())
            except OSError:
                continue
        # Mark initial-seeding done IF the persisted file existed
        # at all (even if every persisted path is now stale / missing
        # → empty `_expanded`).  Otherwise an old-state file with
        # nothing valid in it would silently get the top-level dirs
        # re-expanded on every page load, undoing the user's
        # "collapse all" intent.
        self._initial_done = True

    def _persist_tree_state(self) -> None:
        try:
            self._state_path().write_text(
                json.dumps(
                    {"expanded": sorted(str(p) for p in self._expanded)},
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("could not persist tree state: %s", exc)


__all__ = ["FileTree"]
