"""Drag-and-drop payload schema shared by `editor_view` and
`file_tree`.

The JS-side `dragstart` handlers write a tiny JSON literal to
`dataTransfer`.  The `drop` handlers preprocess it (compute zone,
modifier state) and emit a dict to Python.  This module owns the
schema so the two drop call-sites don't each re-implement the
defensive `.get()` checks on the dict they get back.

Schema fields (all optional in the wire shape, normalised here):

| kind         | source_pane | source_path | source_paths | zone | clone |
|--------------|-------------|-------------|--------------|------|-------|
| `tab`        | pane id     | Path        | (path,)      | str  | bool  |
| `tree-row`   | None        | Path        | tuple[Path]  | None | False |

Callers pattern-match on `kind` to dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

DropKind = Literal["tab", "tree-row"]


@dataclass(frozen=True)
class DropPayload:
    kind: DropKind
    source_path: Path
    source_pane: str | None
    source_paths: tuple[Path, ...]
    zone: str | None
    clone: bool


def parse_drop_payload(args: Any) -> DropPayload | None:
    """Normalise the dict emit()ted from a JS drop handler.

    Returns None for any shape we can't make sense of — the caller
    should treat that as a no-op rather than raising.  NiceGUI in
    some versions wraps a single-arg `emit({...})` as a 1-element
    list; we unwrap.
    """
    if isinstance(args, list):
        if len(args) != 1:
            return None
        args = args[0]
    if not isinstance(args, dict):
        return None

    raw_source_path = args.get("source_path") or args.get("path")
    if not raw_source_path:
        return None

    raw_kind = args.get("type")
    if raw_kind not in ("tab", "tree-row"):
        return None

    source_path = Path(raw_source_path)

    raw_paths = args.get("paths") or args.get("source_paths")
    if raw_paths:
        source_paths = tuple(Path(p) for p in raw_paths)
    else:
        source_paths = (source_path,)

    return DropPayload(
        kind=raw_kind,
        source_path=source_path,
        source_pane=args.get("source_pane") or None,
        source_paths=source_paths,
        zone=args.get("zone") or None,
        clone=bool(args.get("ctrl") or args.get("clone")),
    )


__all__ = ["DropPayload", "DropKind", "parse_drop_payload"]
