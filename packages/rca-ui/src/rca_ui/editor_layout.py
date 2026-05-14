"""Pure-data-model for the editor splits.

`EditorLayout` owns the split tree, per-pane tab lists, and active focus.
It has no dependency on NiceGUI — the UI subscribes to changes and
re-renders the split tree.  Buffer / disk I/O is handled by a separate
`BufferRegistry` (added later in the TDD cycle).

This module is grown one test-driven slice at a time.  Avoid adding
attributes / methods that aren't yet exercised by a test.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

Side = Literal["left", "right", "top", "bottom"]
FileExists = Callable[[Path], bool]
IsDirty = Callable[[Path], bool]


def affected_dirty_tabs(
    paths: list[Path] | tuple[Path, ...],
    *,
    is_dirty: IsDirty,
) -> list[Path]:
    """Filter `paths` keeping only the entries `is_dirty(path)` is True.

    The UI uses this to populate the close-unsaved confirm dialog:
    given the planned set of tabs to close, list the ones that would
    lose unsaved edits."""
    return [p for p in paths if is_dirty(p)]


@dataclass
class _Pane:
    """Internal mutable pane state.  Not part of the public API."""

    id: str
    open_files: list[Path] = field(default_factory=list)
    active_file: Path | None = None


@dataclass
class _Leaf:
    """A leaf in the split tree.  Wraps a pane id."""

    pane_id: str


@dataclass
class _Split:
    """An internal split node.  Children are arranged in `direction`
    order; `ratios` is parallel to `children` and sums to 100."""

    direction: Literal["horizontal", "vertical"]
    children: list["_Leaf | _Split"]
    ratios: list[float]


_TreeNode = "_Leaf | _Split"


@dataclass(frozen=True)
class PaneView:
    """Read-only snapshot of a pane returned by `EditorLayout.pane()`."""

    id: str
    open_files: tuple[Path, ...]
    active_file: Path | None


class EditorLayout:
    """Top-level editor state.  Starts as a single root pane with no
    tabs and no active file."""

    def __init__(self) -> None:
        root = _Pane(id=uuid4().hex)
        self._panes: dict[str, _Pane] = {root.id: root}
        self._root: "_Leaf | _Split" = _Leaf(pane_id=root.id)
        self._active_pane_id: str = root.id

    @property
    def active_pane_id(self) -> str:
        return self._active_pane_id

    def pane(self, pane_id: str) -> PaneView:
        p = self._panes[pane_id]
        return PaneView(
            id=p.id,
            open_files=tuple(p.open_files),
            active_file=p.active_file,
        )

    def open_file(self, pane_id: str, path: Path) -> None:
        """Add `path` to `pane_id`'s tabs (if not already present),
        focus it as the pane's active tab, and make `pane_id` the
        active pane."""
        p = self._panes[pane_id]
        if path not in p.open_files:
            p.open_files.append(path)
        p.active_file = path
        self._active_pane_id = pane_id

    def open_or_reveal(self, path: Path) -> str:
        """Explorer-click entry point.  If `path` is already open in
        any pane, jump focus to the first such pane (and focus the
        tab); otherwise open the file in the currently-active pane.
        Returns the pane id that ended up holding the file."""
        for pane in self._panes.values():
            if path in pane.open_files:
                pane.active_file = path
                self._active_pane_id = pane.id
                return pane.id
        self.open_file(self._active_pane_id, path)
        return self._active_pane_id

    def split(
        self,
        pane_id: str,
        side: Side,
        file: Path | None = None,
        ctrl: bool = False,
    ) -> str:
        """Create a new pane next to `pane_id` on the given side.

        If `file` is supplied:
          - plain (`ctrl=False`) → MOVE that file from source to the
            new pane; source's focus shifts to a neighbour via
            `close_tab` semantics.
          - clone (`ctrl=True`) → KEEP the file in source too; both
            panes' tabs reference the same shared buffer (buffer
            sharing is wired by BufferRegistry, not here).

        The new pane always becomes active.  Returns its id."""
        new_pane = _Pane(id=uuid4().hex)
        self._panes[new_pane.id] = new_pane
        if file is not None:
            if not ctrl:
                self.close_tab(pane_id, file)
            new_pane.open_files.append(file)
            new_pane.active_file = file

        # Splice the new pane into the tree next to the source pane.
        new_leaf = _Leaf(pane_id=new_pane.id)
        direction = "horizontal" if side in ("left", "right") else "vertical"
        if side in ("left", "top"):
            children = [new_leaf, _Leaf(pane_id=pane_id)]
        else:
            children = [_Leaf(pane_id=pane_id), new_leaf]
        split_node = _Split(
            direction=direction, children=children, ratios=[50.0, 50.0]
        )
        # The placeholder leaves above will replace the existing source-
        # pane leaf wherever it lives in the tree.
        found = self._find_leaf(pane_id)
        assert found is not None, f"pane {pane_id} not in tree"
        _, parent, idx = found
        # Reuse the actual source-pane leaf object (avoid stale refs).
        # Locate which child of `split_node` represents the source.
        src_pos = 1 if side in ("left", "top") else 0
        split_node.children[src_pos] = found[0]
        if parent is None:
            self._root = split_node
        else:
            parent.children[idx] = split_node

        self._active_pane_id = new_pane.id
        return new_pane.id

    # ─── serialization ───────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize the current layout to a JSON-compatible dict.
        Schema:
            {
              "active_pane_id": str,
              "root": <node>
            }
            <node> = leaf {type, pane_id, files, active_file}
                   | split {type, direction, ratios, children}"""
        return {
            "active_pane_id": self._active_pane_id,
            "root": self._node_to_dict(self._root),
        }

    def _node_to_dict(self, node: "_Leaf | _Split") -> dict[str, Any]:
        if isinstance(node, _Leaf):
            p = self._panes[node.pane_id]
            return {
                "type": "leaf",
                "pane_id": p.id,
                "files": [str(f) for f in p.open_files],
                "active_file": (
                    str(p.active_file) if p.active_file is not None else None
                ),
            }
        return {
            "type": "split",
            "direction": node.direction,
            "ratios": list(node.ratios),
            "children": [self._node_to_dict(c) for c in node.children],
        }

    @classmethod
    def from_dict(
        cls, blob: dict[str, Any], *, file_exists: FileExists
    ) -> "EditorLayout":
        """Rehydrate a layout from `to_dict()` output.  Files that
        `file_exists(...)` rejects are silently skipped; if a pane
        ends up empty as a result and is not the root leaf, it is
        auto-collapsed (parent split's other child takes the slot)."""
        layout = cls.__new__(cls)
        layout._panes = {}
        layout._active_pane_id = blob["active_pane_id"]
        layout._root = layout._node_from_dict(blob["root"], file_exists)
        # Sweep up any panes that ended up empty after filtering.
        empties = [
            pid for pid, p in layout._panes.items() if not p.open_files
        ]
        for pid in empties:
            layout._collapse_if_non_root(pid)
        # Fallback if active became invalid.
        if layout._active_pane_id not in layout._panes:
            layout._active_pane_id = layout._first_leaf().pane_id
        return layout

    def _node_from_dict(
        self, blob: dict[str, Any], file_exists: FileExists
    ) -> "_Leaf | _Split":
        if blob["type"] == "leaf":
            kept = [Path(f) for f in blob["files"] if file_exists(Path(f))]
            active_blob = blob.get("active_file")
            active_path = Path(active_blob) if active_blob else None
            if active_path is None or active_path not in kept:
                active_path = kept[0] if kept else None
            pane = _Pane(
                id=blob["pane_id"], open_files=kept, active_file=active_path
            )
            self._panes[pane.id] = pane
            return _Leaf(pane_id=pane.id)
        return _Split(
            direction=blob["direction"],
            children=[
                self._node_from_dict(c, file_exists) for c in blob["children"]
            ],
            ratios=list(blob["ratios"]),
        )

    # ─── resize ratios ───────────────────────────────────────────────

    _RATIO_MIN: float = 10.0
    _RATIO_MAX: float = 90.0

    def pane_ratio(self, pane_id: str) -> float | None:
        """Return the % share `pane_id`'s leaf takes in its immediate
        parent split (0–100), or None for the root leaf."""
        found = self._find_leaf(pane_id)
        if found is None:
            return None
        _, parent, idx = found
        if parent is None:
            return None
        return parent.ratios[idx]

    def set_pane_ratio(self, pane_id: str, ratio: float) -> None:
        """Set `pane_id`'s share of its parent split.  Clamped to
        [10, 90] — beyond that the sibling becomes invisibly thin which
        is reliably a UX bug.  Only supports binary splits (every split
        has exactly two children); the sibling absorbs the complement."""
        found = self._find_leaf(pane_id)
        if found is None:
            return
        _, parent, idx = found
        if parent is None:
            return
        clamped = max(self._RATIO_MIN, min(self._RATIO_MAX, ratio))
        parent.ratios[idx] = clamped
        # Binary split invariant — distribute the complement to the
        # one remaining child.  (Splits are 2-ary in this codebase;
        # generalise only when a test demands it.)
        sibling_idx = 1 - idx if len(parent.children) == 2 else None
        if sibling_idx is not None:
            parent.ratios[sibling_idx] = 100.0 - clamped

    def close_others(self, pane_id: str, anchor: Path) -> None:
        """Close every tab in `pane_id` except `anchor`.  Anchor stays
        active."""
        p = self._panes[pane_id]
        if anchor not in p.open_files:
            return
        for path in list(p.open_files):
            if path != anchor:
                self.close_tab(pane_id, path)
        if pane_id in self._panes:
            self._panes[pane_id].active_file = anchor
            self._active_pane_id = pane_id

    def close_saved(self, pane_id: str, *, is_dirty: IsDirty) -> None:
        """Close all CLEAN (not dirty) tabs in `pane_id`, leaving the
        dirty ones open.  Never prompts — it's the one menu entry that
        cannot cause data loss by design."""
        p = self._panes.get(pane_id)
        if p is None:
            return
        for path in list(p.open_files):
            if not is_dirty(path):
                self.close_tab(pane_id, path)

    def close_all(self, pane_id: str) -> None:
        """Close every tab in `pane_id`.  Triggers auto-collapse if
        `pane_id` is not the root leaf."""
        p = self._panes.get(pane_id)
        if p is None:
            return
        for path in list(p.open_files):
            self.close_tab(pane_id, path)

    def close_to_right(self, pane_id: str, anchor: Path) -> None:
        """Close every tab right of `anchor` in `pane_id`'s tab bar.
        The anchor becomes the active tab.  Mirrors VSCode's right-
        click context-menu entry of the same name."""
        self._close_relative(pane_id, anchor, side="right")

    def close_to_left(self, pane_id: str, anchor: Path) -> None:
        """Close every tab left of `anchor` in `pane_id`'s tab bar.
        The anchor becomes the active tab."""
        self._close_relative(pane_id, anchor, side="left")

    def _close_relative(
        self, pane_id: str, anchor: Path, side: Literal["left", "right"]
    ) -> None:
        p = self._panes[pane_id]
        if anchor not in p.open_files:
            return
        anchor_idx = p.open_files.index(anchor)
        if side == "right":
            doomed = list(p.open_files[anchor_idx + 1 :])
        else:
            doomed = list(p.open_files[:anchor_idx])
        for path in doomed:
            self.close_tab(pane_id, path)
        # The anchor must end up active even if it wasn't before.
        if anchor in self._panes.get(pane_id, _Pane(id="")).open_files:
            self._panes[pane_id].active_file = anchor
            self._active_pane_id = pane_id

    def close_tab(self, pane_id: str, path: Path) -> None:
        """Remove `path` from `pane_id`'s tabs.

        - If it was the active tab and the pane still has tabs, focus a
          neighbour (right-of-removed first, left as fallback).
        - If the close empties the pane AND the pane is NOT the root
          leaf of the split tree, auto-collapse it: drop the leaf,
          promote a single-child split's remaining child, retire the
          pane id, and re-focus on whatever pane survives.  Root pane
          stays as an empty placeholder."""
        p = self._panes[pane_id]
        if path not in p.open_files:
            return
        idx = p.open_files.index(path)
        was_active = p.active_file == path
        p.open_files.remove(path)
        if was_active:
            if p.open_files:
                next_idx = (
                    idx if idx < len(p.open_files) else len(p.open_files) - 1
                )
                p.active_file = p.open_files[next_idx]
            else:
                p.active_file = None
        if not p.open_files:
            self._collapse_if_non_root(pane_id)

    # ─── tree helpers ────────────────────────────────────────────────

    def _find_leaf(
        self, pane_id: str
    ) -> tuple["_Leaf", "_Split | None", int] | None:
        """Locate the leaf wrapping `pane_id`.  Returns
        `(leaf, parent_split, index_in_parent)` or None.  Parent is
        None when the leaf is at the tree root."""
        return self._walk(
            lambda n: isinstance(n, _Leaf) and n.pane_id == pane_id
        )

    def _find_node(
        self, target: "_Leaf | _Split"
    ) -> tuple["_Leaf | _Split", "_Split | None", int] | None:
        """Locate `target` by object identity, returning its parent."""
        return self._walk(lambda n: n is target)

    def _walk(
        self,
        predicate,
        node: "_Leaf | _Split | None" = None,
        parent: "_Split | None" = None,
        idx: int = -1,
    ) -> tuple["_Leaf | _Split", "_Split | None", int] | None:
        if node is None:
            node = self._root
        if predicate(node):
            return (node, parent, idx)
        if isinstance(node, _Split):
            for i, child in enumerate(node.children):
                result = self._walk(predicate, child, node, i)
                if result is not None:
                    return result
        return None

    def _first_leaf(self, node: "_Leaf | _Split | None" = None) -> "_Leaf":
        """Pre-order: first leaf reachable from `node` (or root)."""
        n = node if node is not None else self._root
        while isinstance(n, _Split):
            n = n.children[0]
        return n

    def _collapse_if_non_root(self, pane_id: str) -> None:
        """Remove the leaf for `pane_id` from the tree, cascading any
        now-single-child split into its surviving child.  Re-focuses
        on the closest surviving sibling.  No-op if the pane is the
        root leaf."""
        found = self._find_leaf(pane_id)
        if found is None:
            return
        _, parent, idx = found
        if parent is None:
            return  # root leaf: leave as empty placeholder
        parent.children.pop(idx)
        parent.ratios.pop(idx)
        del self._panes[pane_id]
        # Choose the closest sibling subtree BEFORE cascading the
        # parent up: the child that took the removed leaf's index
        # (i.e. the next-right neighbour), or the last child if we
        # just removed the right-most one.  Pre-order into that
        # subtree to land on its first leaf.
        sibling_idx = (
            idx if idx < len(parent.children) else len(parent.children) - 1
        )
        sibling_subtree = parent.children[sibling_idx]
        new_active = self._first_leaf(sibling_subtree).pane_id
        # Cascade: if the split now has exactly one child, promote that
        # child to take the split's slot.
        if len(parent.children) == 1:
            sole = parent.children[0]
            gp_result = self._find_node(parent)
            if gp_result is None or gp_result[1] is None:
                self._root = sole
            else:
                grandparent, gp_idx = gp_result[1], gp_result[2]
                grandparent.children[gp_idx] = sole
        self._active_pane_id = new_active
