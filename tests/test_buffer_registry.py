"""Behaviour tests for the shared-buffer registry.

`BufferRegistry` is the central store for in-memory file contents that
multiple panes can subscribe to.  It owns disk I/O via injected
read/write callables (so tests run without touching the filesystem)
and tracks dirty state per file.  Editing in one pane updates the
buffer; all other subscribed panes are notified so their codemirror
view can sync.
"""

from __future__ import annotations

from pathlib import Path

from rca_ui.buffer_registry import BufferRegistry


# ─── BR-1: subscribe loads disk text and starts clean ───────────────────


def test_subscribe_loads_disk_text_and_is_clean() -> None:
    reg = BufferRegistry(
        read_disk=lambda _p: "hello",
        write_disk=lambda _p, _t: None,
    )

    reg.subscribe(Path("/A.md"), "pane-1")

    assert reg.text(Path("/A.md")) == "hello"
    assert reg.is_dirty(Path("/A.md")) is False


# ─── BR-2: set_text marks the buffer dirty ──────────────────────────────


def test_set_text_marks_buffer_dirty_and_stores_new_text() -> None:
    reg = BufferRegistry(
        read_disk=lambda _p: "old",
        write_disk=lambda _p, _t: None,
    )
    reg.subscribe(Path("/A.md"), "pane-1")

    reg.set_text(Path("/A.md"), "new")

    assert reg.text(Path("/A.md")) == "new"
    assert reg.is_dirty(Path("/A.md")) is True


# ─── BR-3: save writes disk and clears dirty ───────────────────────────


def test_save_writes_disk_text_and_clears_dirty() -> None:
    written: dict[Path, str] = {}

    def writer(p: Path, t: str) -> None:
        written[p] = t

    reg = BufferRegistry(read_disk=lambda _p: "old", write_disk=writer)
    reg.subscribe(Path("/A.md"), "p1")
    reg.set_text(Path("/A.md"), "new")

    reg.save(Path("/A.md"))

    assert written[Path("/A.md")] == "new"
    assert reg.is_dirty(Path("/A.md")) is False


# ─── BR-4: set_text broadcasts a change notification ───────────────────


def test_set_text_broadcasts_change_to_other_subscribers() -> None:
    """An edit in one pane must notify the registry's change hook so
    other subscribers (other panes' codemirror views) can re-sync to
    the new buffer state."""
    notifications: list[Path] = []
    reg = BufferRegistry(
        read_disk=lambda _p: "x",
        write_disk=lambda _p, _t: None,
        on_change=lambda p: notifications.append(p),
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.subscribe(Path("/A.md"), "p2")

    reg.set_text(Path("/A.md"), "edited")

    assert notifications == [Path("/A.md")]


# ─── BR-5: unsubscribe drops the buffer when last subscriber leaves ────


# ─── BR-6: subscribers() lets the UI tell whether closing risks data loss


def test_subscribers_lists_panes_holding_the_buffer() -> None:
    """The UI uses `subscribers(path)` to decide whether closing one
    pane's tab would orphan a dirty buffer.  After unsubscribing one
    of two subscribers, the other one must still appear — so the
    close-modal logic can skip the prompt (the buffer stays alive)."""
    reg = BufferRegistry(
        read_disk=lambda _p: "x", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "pane-1")
    reg.subscribe(Path("/A.md"), "pane-2")
    reg.set_text(Path("/A.md"), "edited")

    reg.unsubscribe(Path("/A.md"), "pane-1")

    assert reg.subscribers(Path("/A.md")) == frozenset({"pane-2"})
    assert reg.is_dirty(Path("/A.md")) is True


def test_unsubscribe_keeps_buffer_until_last_subscriber_leaves() -> None:
    reg = BufferRegistry(
        read_disk=lambda _p: "x", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.subscribe(Path("/A.md"), "p2")
    reg.set_text(Path("/A.md"), "edited")

    reg.unsubscribe(Path("/A.md"), "p1")
    # buffer still alive — other pane still has it
    assert reg.is_dirty(Path("/A.md")) is True

    reg.unsubscribe(Path("/A.md"), "p2")
    # last subscriber gone — buffer removed
    assert reg.is_dirty(Path("/A.md")) is False  # is_dirty returns False for unknown paths
