"""Pure drop dispatch shared by `EditorView._handle_drop`.

The drop event has four meaningful axes:

- **kind**: `tree-row` (file dragged from the explorer) vs `tab` (an
  editor tab being moved within / between split panes).
- **target pane**: the pane the user released the drop on.
- **zone** (tab only): `center` = focus / move into target pane; one
  of `left | right | top | bottom` = create a new pane on that edge
  with the dragged file inside.
- **clone modifier** (tab only): without it the file LEAVES the
  source pane; with it the file is duplicated (shared buffer) into
  the new location.

This module owns the rules; the view layer just calls `apply_drop`.
The `_DropRegistry` Protocol is the minimum surface BufferRegistry
must expose for the coordinator's needs — concrete BufferRegistry
satisfies it structurally.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from rca_ui.editor_layout import EditorLayout
from rca_ui.ui._drag_payload import DropPayload


class _DropRegistry(Protocol):
    def subscribe(self, path: Path, pane_id: str) -> None: ...
    def unsubscribe(self, path: Path, pane_id: str) -> None: ...


def apply_drop(
    layout: EditorLayout,
    registry: _DropRegistry,
    target_pane_id: str,
    payload: DropPayload,
) -> bool:
    """Mutate `layout` and `registry` according to `payload`.

    Returns True when anything changed (caller can decide whether
    to re-render / persist).  Returns False on unrecognised payloads,
    missing / stale pane ids, or a no-op (e.g. tab dragged onto its
    own pane's only-file in a way that would auto-collapse).
    """
    if not layout.has_pane(target_pane_id):
        return False

    if payload.kind == "tree-row":
        return _apply_tree_row(layout, registry, target_pane_id, payload)
    if payload.kind == "tab":
        return _apply_tab(layout, registry, target_pane_id, payload)
    return False


# ─── tree row → editor pane ───────────────────────────────────────────


def _apply_tree_row(
    layout: EditorLayout,
    registry: _DropRegistry,
    target_pid: str,
    payload: DropPayload,
) -> bool:
    path = payload.source_path
    before = path in layout.pane(target_pid).open_files
    layout.open_file(target_pid, path, preview=False)
    if not before:
        registry.subscribe(path, target_pid)
    return True


# ─── editor tab → editor pane ─────────────────────────────────────────


def _apply_tab(
    layout: EditorLayout,
    registry: _DropRegistry,
    target_pid: str,
    payload: DropPayload,
) -> bool:
    source_pid = payload.source_pane
    if source_pid is None or not layout.has_pane(source_pid):
        return False
    zone = payload.zone
    if zone == "center":
        return _drop_center(
            layout, registry, target_pid, source_pid,
            payload.source_path, payload.clone,
        )
    if zone in ("left", "right", "top", "bottom"):
        return _drop_edge(
            layout, registry, target_pid, source_pid,
            payload.source_path, zone, payload.clone,
        )
    return False


def _drop_center(
    layout: EditorLayout,
    registry: _DropRegistry,
    target_pid: str,
    source_pid: str,
    path: Path,
    clone: bool,
) -> bool:
    if target_pid == source_pid:
        # Same pane → idempotent focus (open_file refreshes active).
        layout.open_file(target_pid, path)
        return True
    if not clone:
        layout.close_tab(source_pid, path)
        registry.unsubscribe(path, source_pid)
    before = path in layout.pane(target_pid).open_files
    layout.open_file(target_pid, path)
    if not before:
        registry.subscribe(path, target_pid)
    return True


def _drop_edge(
    layout: EditorLayout,
    registry: _DropRegistry,
    target_pid: str,
    source_pid: str,
    path: Path,
    side: str,
    clone: bool,
) -> bool:
    # Same-pane edge drop where `path` is the pane's ONLY tab: moving
    # it out would empty + auto-collapse the source pane, leaving the
    # split anchorless.  Treat as no-op.
    if source_pid == target_pid and not clone:
        src_files = layout.pane(source_pid).open_files
        if len(src_files) == 1 and src_files[0] == path:
            return False

    if not clone and source_pid != target_pid:
        layout.close_tab(source_pid, path)
        registry.unsubscribe(path, source_pid)

    if not clone and source_pid == target_pid:
        new_pid = layout.split(source_pid, side=side, file=path, ctrl=False)  # type: ignore[arg-type]
        registry.unsubscribe(path, source_pid)
        registry.subscribe(path, new_pid)
        return True

    new_pid = layout.split(target_pid, side=side, file=path, ctrl=True)  # type: ignore[arg-type]
    registry.subscribe(path, new_pid)
    return True


__all__ = ["apply_drop"]
