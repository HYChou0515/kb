"""Drop coordination — a pure function over EditorLayout + a
registry-protocol that handles every drop scenario: file-tree row
dropped on a pane, editor tab moved within / across panes (center
zone), tab split into a new pane (edge zone), and the clone modifier.

The function is the test surface for drop semantics; EditorView's
remaining `_handle_drop` is a 5-line dispatch wrapper.
"""

from __future__ import annotations

from pathlib import Path

from rca_ui.editor_layout import EditorLayout
from rca_ui.ui._drag_payload import DropPayload
from rca_ui.ui._drop_coordinator import apply_drop


class _StubRegistry:
    """Records subscribe/unsubscribe calls in order.  Mirrors the
    Protocol that BufferRegistry satisfies at the drop-coordinator
    seam."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Path, str]] = []

    def subscribe(self, path: Path, pane_id: str) -> None:
        self.calls.append(("sub", path, pane_id))

    def unsubscribe(self, path: Path, pane_id: str) -> None:
        self.calls.append(("unsub", path, pane_id))


def _tree_row(path: Path) -> DropPayload:
    return DropPayload(
        kind="tree-row",
        source_path=path,
        source_pane=None,
        source_paths=(path,),
        zone=None,
        clone=False,
    )


def _tab(
    source_pane: str, path: Path, zone: str, *, clone: bool = False
) -> DropPayload:
    return DropPayload(
        kind="tab",
        source_path=path,
        source_pane=source_pane,
        source_paths=(path,),
        zone=zone,
        clone=clone,
    )


# ─── DC-1: tree-row dropped on a pane subscribes + opens ───────────────


def test_tree_row_drop_subscribes_and_opens_persistent() -> None:
    """Single-click in the tree opens preview; explicit drag is a
    stronger signal so the tab opens persistent (no italic)."""
    layout = EditorLayout()
    target = layout.active_pane_id
    reg = _StubRegistry()

    changed = apply_drop(
        layout, reg, target, _tree_row(Path("/A.md"))
    )

    assert changed is True
    pane = layout.pane(target)
    assert list(pane.open_files) == [Path("/A.md")]
    assert pane.preview_file is None
    assert reg.calls == [("sub", Path("/A.md"), target)]


def test_tree_row_drop_when_file_already_open_only_focuses() -> None:
    """Dragging the same file onto its own pane is a focus action —
    no new subscribe (would double the subscriber count)."""
    layout = EditorLayout()
    target = layout.active_pane_id
    layout.open_file(target, Path("/A.md"))
    reg = _StubRegistry()

    changed = apply_drop(layout, reg, target, _tree_row(Path("/A.md")))

    assert changed is True  # active focus changed (idempotent open)
    assert reg.calls == []


# ─── DC-2: tab drop center same pane is a no-op (focus only) ──────────


def test_tab_drop_center_on_own_pane_is_idempotent() -> None:
    """No subscribe / unsubscribe — and the file stays in the same
    spot of the tab bar."""
    layout = EditorLayout()
    p = layout.active_pane_id
    layout.open_file(p, Path("/A.md"))
    reg = _StubRegistry()

    apply_drop(layout, reg, p, _tab(p, Path("/A.md"), "center"))

    assert list(layout.pane(p).open_files) == [Path("/A.md")]
    assert reg.calls == []


# ─── DC-3: tab drop center cross-pane moves the file ─────────────────


def test_tab_drop_center_cross_pane_move() -> None:
    """No clone modifier → file leaves source, lands on target.
    Source pane keeps its OTHER tabs; if the dragged file was the
    source's only tab the pane auto-collapses (close_tab semantics)."""
    layout = EditorLayout()
    a = layout.active_pane_id
    layout.open_file(a, Path("/A.md"))
    layout.open_file(a, Path("/B.md"))  # a has [A, B]
    b = layout.split(a, "right")  # active is now b
    reg = _StubRegistry()

    apply_drop(layout, reg, b, _tab(a, Path("/A.md"), "center"))

    assert list(layout.pane(a).open_files) == [Path("/B.md")]
    assert list(layout.pane(b).open_files) == [Path("/A.md")]
    assert reg.calls == [
        ("unsub", Path("/A.md"), a),
        ("sub", Path("/A.md"), b),
    ]


def test_tab_drop_center_cross_pane_clone_keeps_source() -> None:
    """Ctrl/Alt held → both panes end up with the file (shared
    buffer)."""
    layout = EditorLayout()
    a = layout.active_pane_id
    layout.open_file(a, Path("/A.md"))
    b = layout.split(a, "right")
    reg = _StubRegistry()

    apply_drop(
        layout, reg, b, _tab(a, Path("/A.md"), "center", clone=True),
    )

    assert list(layout.pane(a).open_files) == [Path("/A.md")]
    assert list(layout.pane(b).open_files) == [Path("/A.md")]
    assert reg.calls == [("sub", Path("/A.md"), b)]


# ─── DC-4: tab drop edge splits ───────────────────────────────────────


def test_tab_drop_edge_creates_new_pane_with_file() -> None:
    """Edge drop → new pane neighbours the target.  File moves into
    the new pane and is subscribed there."""
    layout = EditorLayout()
    a = layout.active_pane_id
    layout.open_file(a, Path("/A.md"))
    layout.open_file(a, Path("/B.md"))
    reg = _StubRegistry()

    apply_drop(layout, reg, a, _tab(a, Path("/A.md"), "right"))

    # A moved out of pane a — only B remains there.
    assert list(layout.pane(a).open_files) == [Path("/B.md")]
    # A ended up in the newly-active pane.
    new_pid = layout.active_pane_id
    assert new_pid != a
    assert list(layout.pane(new_pid).open_files) == [Path("/A.md")]


# ─── DC-5: invariants — unknown target, missing source ───────────────


def test_drop_returns_false_when_target_pane_missing() -> None:
    layout = EditorLayout()
    reg = _StubRegistry()

    assert apply_drop(
        layout, reg, "ghost", _tree_row(Path("/A.md"))
    ) is False
    assert reg.calls == []


def test_tab_drop_returns_false_when_source_pane_missing() -> None:
    layout = EditorLayout()
    target = layout.active_pane_id
    reg = _StubRegistry()

    assert apply_drop(
        layout, reg, target,
        _tab("ghost", Path("/A.md"), "center"),
    ) is False
    assert reg.calls == []
