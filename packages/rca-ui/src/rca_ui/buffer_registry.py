"""Shared-buffer store for the editor.

Each open file has one in-memory buffer that any number of panes can
subscribe to.  When pane A edits, the buffer's `current_text` updates
and all other subscribers are notified — their codemirror views can
re-sync to the new content while keeping their own cursor / scroll
state.  Saving writes `current_text` back to disk; subsequent
`is_dirty(path)` returns False until the next edit.

Disk I/O is injected (`read_disk`, `write_disk`) so unit tests don't
touch the filesystem.  Callers wire the real `Path.read_text` /
`Path.write_text` in production.

Grown one TDD slice at a time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class _BufferState:
    path: Path
    disk_text: str
    current_text: str
    subscribers: set[str] = field(default_factory=set)

    @property
    def is_dirty(self) -> bool:
        return self.current_text != self.disk_text


class BufferRegistry:
    """Manages the lifecycle of shared in-memory buffers.

    `read_disk(path) -> str` and `write_disk(path, text)` are injected
    so the registry has no direct filesystem dependency."""

    def __init__(
        self,
        *,
        read_disk: Callable[[Path], str],
        write_disk: Callable[[Path, str], None],
        on_change: Callable[[Path], None] | None = None,
    ) -> None:
        self._read_disk = read_disk
        self._write_disk = write_disk
        self._on_change = on_change
        self._buffers: dict[Path, _BufferState] = {}

    def subscribe(self, path: Path, pane_id: str) -> None:
        """Register `pane_id` as a subscriber of `path`'s buffer,
        loading the file from disk on the first subscriber."""
        if path not in self._buffers:
            disk_text = self._read_disk(path)
            self._buffers[path] = _BufferState(
                path=path,
                disk_text=disk_text,
                current_text=disk_text,
                subscribers={pane_id},
            )
        else:
            self._buffers[path].subscribers.add(pane_id)

    def unsubscribe(self, path: Path, pane_id: str) -> None:
        """Drop `pane_id` from `path`'s subscribers.  When the last
        subscriber leaves, the buffer is released."""
        b = self._buffers.get(path)
        if b is None:
            return
        b.subscribers.discard(pane_id)
        if not b.subscribers:
            del self._buffers[path]

    def text(self, path: Path) -> str:
        """Latest in-memory text (may be ahead of disk if dirty)."""
        return self._buffers[path].current_text

    def set_text(self, path: Path, new_text: str) -> None:
        """Replace a buffer's current text.  Broadcasts `on_change(path)`
        so subscribers other than the editor that triggered this can
        re-sync their views."""
        b = self._buffers[path]
        if b.current_text == new_text:
            return
        b.current_text = new_text
        if self._on_change is not None:
            self._on_change(path)

    def save(self, path: Path) -> None:
        """Persist `path`'s current text to disk via `write_disk`.
        Clears the dirty flag for all subscribers (they all see the
        single shared `disk_text` flip)."""
        b = self._buffers[path]
        self._write_disk(path, b.current_text)
        b.disk_text = b.current_text

    def is_dirty(self, path: Path) -> bool:
        """Whether `path`'s buffer has unsaved edits.  False if no
        buffer exists for the path."""
        b = self._buffers.get(path)
        return b is not None and b.is_dirty

    def subscribers(self, path: Path) -> frozenset[str]:
        """Pane ids subscribed to `path`'s buffer.  Returns an empty
        frozenset when no buffer exists for the path.

        Used by the close-confirm flow: closing a pane's tab is safe
        (no modal) when at least one OTHER subscriber will remain after
        the close, even if the buffer is currently dirty."""
        b = self._buffers.get(path)
        return frozenset(b.subscribers) if b is not None else frozenset()
