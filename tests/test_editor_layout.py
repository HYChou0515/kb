"""Behaviour tests for the pure-data-model layer of the editor splits.

The model under test (`rca_ui.editor_layout.EditorLayout`) is the Python
object that owns the split tree, per-pane tab lists, active focus, and
the operations that mutate them.  It has *no* dependency on NiceGUI —
the UI layer subscribes to changes and re-renders.

Tests are vertical slices: one behaviour, one minimal implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rca_ui.editor_layout import EditorLayout, affected_dirty_tabs


# ─── #1: open file → tab appears, becomes active ────────────────────────


def test_open_file_in_pane_adds_tab_and_focuses_it() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id

    layout.open_file(pane_id, Path("/case/CASE.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/case/CASE.md")]
    assert pane.active_file == Path("/case/CASE.md")


# ─── #2: re-open existing file in same pane → focus, no duplicate ───────


def test_reopen_existing_file_focuses_without_duplicating() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/case/A.md"))
    layout.open_file(pane_id, Path("/case/B.md"))

    # Re-open A — must NOT append a second tab, must re-focus it.
    layout.open_file(pane_id, Path("/case/A.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [
        Path("/case/A.md"),
        Path("/case/B.md"),
    ]
    assert pane.active_file == Path("/case/A.md")


# ─── #4: close a tab → focus moves to a sensible neighbour ──────────────


def test_close_active_last_tab_focuses_previous() -> None:
    """Closing the right-most active tab moves focus left."""
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/A.md"))
    layout.open_file(pane_id, Path("/B.md"))
    layout.open_file(pane_id, Path("/C.md"))  # active = C (right-most)

    layout.close_tab(pane_id, Path("/C.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/A.md"), Path("/B.md")]
    assert pane.active_file == Path("/B.md")


def test_close_active_middle_tab_focuses_right_neighbour() -> None:
    """Closing a middle active tab moves focus to the right."""
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/A.md"))
    layout.open_file(pane_id, Path("/B.md"))
    layout.open_file(pane_id, Path("/C.md"))
    layout.open_file(pane_id, Path("/B.md"))  # re-focus B (middle)

    layout.close_tab(pane_id, Path("/B.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/A.md"), Path("/C.md")]
    assert pane.active_file == Path("/C.md")


def test_close_inactive_tab_keeps_focus() -> None:
    """Closing a non-active tab leaves the active focus untouched."""
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/A.md"))
    layout.open_file(pane_id, Path("/B.md"))  # active = B

    layout.close_tab(pane_id, Path("/A.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/B.md")]
    assert pane.active_file == Path("/B.md")


# ─── #9: split pane → new sibling pane with the moved file ──────────────


def test_split_pane_right_moves_file_to_new_pane_and_focuses_it() -> None:
    """Plain split (no ctrl) MOVES the file out of the source pane
    into a brand-new pane on the chosen side.  The new pane becomes
    active.  Source keeps its remaining tabs."""
    layout = EditorLayout()
    src = layout.active_pane_id
    layout.open_file(src, Path("/A.md"))
    layout.open_file(src, Path("/B.md"))  # active = B in src

    new_pane_id = layout.split(src, side="right", file=Path("/A.md"))

    assert new_pane_id != src
    assert layout.active_pane_id == new_pane_id

    src_view = layout.pane(src)
    new_view = layout.pane(new_pane_id)
    assert list(src_view.open_files) == [Path("/B.md")]
    assert src_view.active_file == Path("/B.md")
    assert list(new_view.open_files) == [Path("/A.md")]
    assert new_view.active_file == Path("/A.md")


# ─── #3: open existing file in another pane → jump focus to it ─────────


def test_open_or_reveal_jumps_to_existing_pane_with_file() -> None:
    """`open_or_reveal(path)` is the Explorer-click entry point: if the
    file is already open in ANY pane, focus that pane + tab; otherwise
    open in the currently-active pane.

    Here B is in pane_b (active).  Calling open_or_reveal on A (in
    pane_a) must jump focus to pane_a, not duplicate A into pane_b."""
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/B.md"))
    # State: pane_a → [A.md], pane_b → [B.md]; active = pane_b.

    layout.open_or_reveal(Path("/A.md"))

    assert layout.active_pane_id == pane_a
    assert layout.pane(pane_a).active_file == Path("/A.md")
    # No new tab in pane_b.
    assert list(layout.pane(pane_b).open_files) == [Path("/B.md")]


def test_open_or_reveal_opens_in_active_pane_when_file_not_open_anywhere() -> None:
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    pane_b = layout.split(pane_a, side="right")  # empty new pane, active

    layout.open_or_reveal(Path("/X.md"))

    assert layout.active_pane_id == pane_b
    pane = layout.pane(pane_b)
    assert list(pane.open_files) == [Path("/X.md")]
    assert pane.active_file == Path("/X.md")


def test_split_with_ctrl_keeps_file_in_both_panes() -> None:
    """Ctrl-drag split is a CLONE: the file is added to the new pane
    but stays in the source pane too (both tabs reference the same
    shared buffer — buffer wiring is a separate concern)."""
    layout = EditorLayout()
    src = layout.active_pane_id
    layout.open_file(src, Path("/A.md"))

    new_pane_id = layout.split(
        src, side="right", file=Path("/A.md"), ctrl=True
    )

    src_view = layout.pane(src)
    new_view = layout.pane(new_pane_id)
    assert list(src_view.open_files) == [Path("/A.md")]  # KEPT in source
    assert src_view.active_file == Path("/A.md")
    assert list(new_view.open_files) == [Path("/A.md")]
    assert new_view.active_file == Path("/A.md")
    assert layout.active_pane_id == new_pane_id


# ─── #7: close last tab in the *root* pane → stay as empty placeholder ──


# ─── #5: close last tab in non-root pane → auto-collapse pane ──────────


# ─── #6: cascade — parent split with 1 remaining child collapses too ───


def test_cascade_collapse_promotes_lone_sibling_to_parent_slot() -> None:
    """Three-pane row [A | B | C] is two nested splits:
        outer = [leaf_a, inner]
        inner = [leaf_b, leaf_c]
    Closing C makes `inner` a single-child split → it must be replaced
    by `leaf_b` in `outer`, giving [leaf_a, leaf_b].  Both A and B must
    survive."""
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/B.md"))
    pane_c = layout.split(pane_b, side="right", file=Path("/C.md"))

    layout.close_tab(pane_c, Path("/C.md"))

    with pytest.raises(KeyError):
        layout.pane(pane_c)
    assert layout.pane(pane_a).active_file == Path("/A.md")
    assert layout.pane(pane_b).active_file == Path("/B.md")


# ─── #8: collapse → focus closest sibling (not pre-order first leaf) ───


def test_collapse_focuses_closest_sibling_not_far_pane() -> None:
    """In a [A | B | C] row, closing C (rightmost) must shift focus
    to B (its immediate sibling), not back to A.  Pre-order would
    naively pick A — this test guards against that regression."""
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/B.md"))
    pane_c = layout.split(pane_b, side="right", file=Path("/C.md"))

    layout.close_tab(pane_c, Path("/C.md"))

    assert layout.active_pane_id == pane_b


def test_close_last_tab_in_non_root_pane_collapses_pane() -> None:
    """In a [A | B] split, closing B's last tab makes pane_b
    disappear from the tree; pane_a inherits the full area and
    becomes active."""
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/B.md"))

    layout.close_tab(pane_b, Path("/B.md"))

    # pane_b is collapsed → no longer queryable.
    with pytest.raises(KeyError):
        layout.pane(pane_b)
    # pane_a survives and is the new active.
    assert layout.active_pane_id == pane_a
    pane = layout.pane(pane_a)
    assert list(pane.open_files) == [Path("/A.md")]
    assert pane.active_file == Path("/A.md")


# ─── #16: close to the right / left of an anchor tab ────────────────────


def test_close_to_right_keeps_anchor_and_earlier_tabs() -> None:
    """Right-clicking B in [A, B, C, D] → "Close to the Right" closes
    C and D, leaves [A, B], and focuses the anchor B."""
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    for name in "ABCD":
        layout.open_file(pane_id, Path(f"/{name}.md"))

    layout.close_to_right(pane_id, Path("/B.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/A.md"), Path("/B.md")]
    assert pane.active_file == Path("/B.md")


def test_close_to_left_keeps_anchor_and_later_tabs() -> None:
    """Right-clicking C in [A, B, C, D] → "Close to the Left" closes
    A and B, leaves [C, D], and focuses the anchor C."""
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    for name in "ABCD":
        layout.open_file(pane_id, Path(f"/{name}.md"))

    layout.close_to_left(pane_id, Path("/C.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/C.md"), Path("/D.md")]
    assert pane.active_file == Path("/C.md")


# ─── #17: close others / close all ──────────────────────────────────────


def test_close_others_keeps_only_anchor() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    for name in "ABC":
        layout.open_file(pane_id, Path(f"/{name}.md"))

    layout.close_others(pane_id, Path("/B.md"))

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [Path("/B.md")]
    assert pane.active_file == Path("/B.md")


def test_close_all_in_root_pane_empties_it_without_removing() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    for name in "ABC":
        layout.open_file(pane_id, Path(f"/{name}.md"))

    layout.close_all(pane_id)

    pane = layout.pane(pane_id)
    assert pane.open_files == ()
    assert pane.active_file is None
    assert layout.active_pane_id == pane_id  # root pane stays


def test_close_all_collapses_non_root_pane() -> None:
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/B.md"))
    layout.open_file(pane_b, Path("/B2.md"))

    layout.close_all(pane_b)

    with pytest.raises(KeyError):
        layout.pane(pane_b)
    assert layout.active_pane_id == pane_a


# ─── #20: resize ratio is clamped to [10, 90] ───────────────────────────


def test_set_pane_ratio_updates_both_sides_of_split() -> None:
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    pane_b = layout.split(pane_a, side="right")

    layout.set_pane_ratio(pane_b, 70)

    assert layout.pane_ratio(pane_b) == 70.0
    assert layout.pane_ratio(pane_a) == 30.0


def test_set_pane_ratio_clamps_below_min_to_10() -> None:
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    pane_b = layout.split(pane_a, side="right")

    layout.set_pane_ratio(pane_b, 5)

    assert layout.pane_ratio(pane_b) == 10.0
    assert layout.pane_ratio(pane_a) == 90.0


def test_set_pane_ratio_clamps_above_max_to_90() -> None:
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    pane_b = layout.split(pane_a, side="right")

    layout.set_pane_ratio(pane_b, 95)

    assert layout.pane_ratio(pane_b) == 90.0
    assert layout.pane_ratio(pane_a) == 10.0


# ─── #18: serialize / deserialize the split tree ────────────────────────


def _always_exists(_p: Path) -> bool:
    return True


def test_to_dict_from_dict_roundtrips_single_pane() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/A.md"))
    layout.open_file(pane_id, Path("/B.md"))
    # state: [A, B] active=B in single root pane

    blob = layout.to_dict()
    restored = EditorLayout.from_dict(blob, file_exists=_always_exists)

    assert restored.active_pane_id == pane_id
    pane = restored.pane(pane_id)
    assert list(pane.open_files) == [Path("/A.md"), Path("/B.md")]
    assert pane.active_file == Path("/B.md")


def test_to_dict_from_dict_roundtrips_split_layout() -> None:
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    layout.open_file(pane_a, Path("/X.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/B.md"))
    layout.set_pane_ratio(pane_b, 60)
    # state: [A,X|act=X] right [B|act=B] @60% pane_b active

    blob = layout.to_dict()
    restored = EditorLayout.from_dict(blob, file_exists=_always_exists)

    assert restored.active_pane_id == pane_b
    assert list(restored.pane(pane_a).open_files) == [
        Path("/A.md"),
        Path("/X.md"),
    ]
    assert restored.pane(pane_a).active_file == Path("/X.md")
    assert list(restored.pane(pane_b).open_files) == [Path("/B.md")]
    assert restored.pane(pane_b).active_file == Path("/B.md")
    assert restored.pane_ratio(pane_b) == 60.0
    assert restored.pane_ratio(pane_a) == 40.0


# ─── #19: deserialize — skip missing files, collapse emptied panes ─────


def test_deserialize_silently_skips_missing_files() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/A.md"))
    layout.open_file(pane_id, Path("/MISSING.md"))
    layout.open_file(pane_id, Path("/B.md"))  # active = B

    blob = layout.to_dict()

    def exists(p: Path) -> bool:
        return p != Path("/MISSING.md")

    restored = EditorLayout.from_dict(blob, file_exists=exists)
    pane = restored.pane(pane_id)
    assert list(pane.open_files) == [Path("/A.md"), Path("/B.md")]
    assert pane.active_file == Path("/B.md")  # B was the active one


def test_deserialize_empty_non_root_pane_auto_collapses() -> None:
    """If every file in a non-root pane is missing on reload, that
    pane is treated as if all its tabs were closed: cascade-collapse
    out of the split tree."""
    layout = EditorLayout()
    pane_a = layout.active_pane_id
    layout.open_file(pane_a, Path("/A.md"))
    pane_b = layout.split(pane_a, side="right", file=Path("/GONE.md"))

    blob = layout.to_dict()
    restored = EditorLayout.from_dict(
        blob, file_exists=lambda p: p != Path("/GONE.md")
    )

    with pytest.raises(KeyError):
        restored.pane(pane_b)
    assert restored.active_pane_id == pane_a
    assert restored.pane(pane_a).active_file == Path("/A.md")


# ─── #15: close saved (keeps dirty ones) ───────────────────────────────


def test_close_saved_closes_clean_tabs_keeps_dirty_ones() -> None:
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/clean1.md"))
    layout.open_file(pane_id, Path("/dirty1.md"))
    layout.open_file(pane_id, Path("/clean2.md"))
    layout.open_file(pane_id, Path("/dirty2.md"))

    dirty = {Path("/dirty1.md"), Path("/dirty2.md")}
    layout.close_saved(pane_id, is_dirty=lambda p: p in dirty)

    pane = layout.pane(pane_id)
    assert list(pane.open_files) == [
        Path("/dirty1.md"),
        Path("/dirty2.md"),
    ]


# ─── #14: affected_dirty_tabs filters paths by is_dirty ────────────────


def test_affected_dirty_tabs_returns_only_dirty_paths_in_order() -> None:
    paths = [Path("/A.md"), Path("/B.md"), Path("/C.md"), Path("/D.md")]
    dirty = {Path("/B.md"), Path("/D.md")}

    result = affected_dirty_tabs(paths, is_dirty=lambda p: p in dirty)

    assert result == [Path("/B.md"), Path("/D.md")]


def test_close_last_tab_in_root_pane_leaves_pane_empty() -> None:
    """The root pane is special: closing its last tab must NOT remove
    the pane.  It stays as an empty placeholder ("Select a file…").
    `active_file` becomes None but the pane id is still valid and
    still active."""
    layout = EditorLayout()
    pane_id = layout.active_pane_id
    layout.open_file(pane_id, Path("/A.md"))

    layout.close_tab(pane_id, Path("/A.md"))

    assert layout.active_pane_id == pane_id  # still the active pane
    pane = layout.pane(pane_id)  # still queryable → not removed
    assert pane.open_files == ()
    assert pane.active_file is None
