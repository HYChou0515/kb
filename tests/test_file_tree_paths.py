"""Path-math used by FileTree.reveal — pure, no NiceGUI dependency."""
from __future__ import annotations

from pathlib import Path

from rca_ui.ui.file_tree import _parents_to_expand


def test_parents_for_nested_file(tmp_path: Path) -> None:
    """A file two levels deep produces both intermediate dirs in
    workspace-relative order (outer first)."""
    nested = tmp_path / "outer" / "inner" / "file.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")

    parents = _parents_to_expand(tmp_path, nested)

    assert parents == [
        (tmp_path / "outer").resolve(),
        (tmp_path / "outer" / "inner").resolve(),
    ]


def test_parents_for_direct_child_is_empty(tmp_path: Path) -> None:
    """Files directly under the workspace have no intermediate dirs
    to open — return empty so reveal is a no-op for root files."""
    direct = tmp_path / "CASE.md"
    direct.write_text("x", encoding="utf-8")

    assert _parents_to_expand(tmp_path, direct) == []


def test_parents_for_path_outside_workspace_is_empty(tmp_path: Path) -> None:
    """A file outside the workspace can't be revealed; return empty
    rather than blowing up.  Lets the caller treat reveal as best-
    effort."""
    outside = tmp_path.parent / "elsewhere.md"

    assert _parents_to_expand(tmp_path, outside) == []
