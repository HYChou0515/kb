"""Drop-event payload parsing — the dict emit()ted from the JS drop
handlers is normalised into a typed `DropPayload` so editor_view and
file_tree don't each re-implement defensive `.get()` checks.
"""

from __future__ import annotations

from pathlib import Path

from rca_ui.ui._drag_payload import DropPayload, parse_drop_payload


# ─── DP-1: editor tab drop shape ───────────────────────────────────────


def test_parse_editor_tab_drop_emit() -> None:
    """Tab dragged in the editor → JS handler computes zone + ctrl
    from cursor / modifier state and emits this dict shape."""
    args = {
        "type": "tab",
        "source_pane": "abc123",
        "source_path": "/case1/A.md",
        "zone": "right",
        "ctrl": True,
    }

    payload = parse_drop_payload(args)

    assert payload == DropPayload(
        kind="tab",
        source_path=Path("/case1/A.md"),
        source_pane="abc123",
        source_paths=(Path("/case1/A.md"),),
        zone="right",
        clone=True,
    )


# ─── DP-2: file-tree row drop shape ────────────────────────────────────


def test_parse_tree_row_drop_emit() -> None:
    """Tree row dragstart emits a literal JSON with `paths` for multi-
    drag.  Whether the drop target is another tree row or an editor
    pane, the same parser handles it."""
    args = {
        "type": "tree-row",
        "path": "/case1/A.md",
        "paths": ["/case1/A.md", "/case1/B.md"],
    }

    payload = parse_drop_payload(args)

    assert payload == DropPayload(
        kind="tree-row",
        source_path=Path("/case1/A.md"),
        source_pane=None,
        source_paths=(Path("/case1/A.md"), Path("/case1/B.md")),
        zone=None,
        clone=False,
    )


# ─── DP-3: NiceGUI single-arg list wrapper ─────────────────────────────


def test_parse_unwraps_single_arg_list() -> None:
    """NiceGUI emits a single-arg `emit({...})` as a 1-element list in
    some versions.  The parser must accept both shapes."""
    args = [{
        "type": "tab",
        "source_pane": "p1",
        "source_path": "/A.md",
        "zone": "center",
        "ctrl": False,
    }]

    payload = parse_drop_payload(args)

    assert payload is not None
    assert payload.kind == "tab"
    assert payload.source_pane == "p1"


# ─── DP-4: malformed → None (caller treats as no-op) ───────────────────


def test_parse_returns_none_for_missing_source_path() -> None:
    """No source_path → nothing to drop.  Don't raise — drop handlers
    fire from JS and we can't risk crashing on a partial event."""
    assert parse_drop_payload({"type": "tab", "zone": "left"}) is None


def test_parse_returns_none_for_unknown_args_shape() -> None:
    assert parse_drop_payload(None) is None
    assert parse_drop_payload("not a dict") is None
    assert parse_drop_payload([]) is None


# ─── DP-5: source_paths falls back to [source_path] ────────────────────


def test_source_paths_singleton_when_paths_missing() -> None:
    """Tab drops have `source_path` only (no array).  The parser
    fills `source_paths=(source_path,)` so callers don't need to
    special-case singleton vs multi-drag."""
    args = {
        "type": "tab",
        "source_pane": "p1",
        "source_path": "/A.md",
        "zone": "center",
        "ctrl": False,
    }

    payload = parse_drop_payload(args)

    assert payload is not None
    assert payload.source_paths == (Path("/A.md"),)
