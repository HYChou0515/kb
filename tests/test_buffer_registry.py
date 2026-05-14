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


# ─── BR-7: mark_deleted keeps the buffer alive, dirty, and tagged ───────


def test_mark_deleted_keeps_buffer_alive_and_dirty() -> None:
    """When the user (or the agent) deletes the file underneath an
    open buffer, the editor tab stays open as a strike-through
    orphan: the in-memory text is preserved, the buffer is
    permanently dirty (you have to Save to get it back to disk),
    and it advertises itself via `is_deleted`."""
    reg = BufferRegistry(
        read_disk=lambda _p: "hello", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")

    reg.mark_deleted(Path("/A.md"))

    assert reg.is_deleted(Path("/A.md")) is True
    # text is preserved exactly as it was when the file vanished
    assert reg.text(Path("/A.md")) == "hello"
    # always dirty while deleted — no comparison against a missing disk
    assert reg.is_dirty(Path("/A.md")) is True


# ─── BR-8: save resurrects a deleted buffer to its original path ────────


def test_save_resurrects_deleted_buffer_to_original_path() -> None:
    """Save on a deleted buffer writes back to the original path and
    clears the deleted flag — the file is "undeleted" through the
    editor, no save-as prompt required."""
    written: dict[Path, str] = {}
    reg = BufferRegistry(
        read_disk=lambda _p: "hello",
        write_disk=lambda p, t: written.__setitem__(p, t),
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.set_text(Path("/A.md"), "edited")
    reg.mark_deleted(Path("/A.md"))

    reg.save(Path("/A.md"))

    assert written[Path("/A.md")] == "edited"
    assert reg.is_deleted(Path("/A.md")) is False
    assert reg.is_dirty(Path("/A.md")) is False


# ─── BR-9: reload_disk_text picks up external changes ──────────────────


def test_reload_disk_text_updates_clean_buffer_in_place() -> None:
    """After the agent's turn finishes, the host calls
    `reload_disk_text(path)` on every subscribed buffer.  For a
    clean buffer that means refreshing both `disk_text` and the
    in-memory text — the UI then re-renders the codemirror view."""
    disk_state = {"text": "v1"}
    notifications: list[Path] = []
    reg = BufferRegistry(
        read_disk=lambda _p: disk_state["text"],
        write_disk=lambda _p, _t: None,
        on_change=lambda p: notifications.append(p),
    )
    reg.subscribe(Path("/A.md"), "p1")
    assert reg.text(Path("/A.md")) == "v1"
    notifications.clear()

    disk_state["text"] = "v2"
    reg.reload_disk_text(Path("/A.md"))

    assert reg.text(Path("/A.md")) == "v2"
    assert reg.is_dirty(Path("/A.md")) is False
    # subscribers need to know so their codemirror views can refresh.
    assert notifications == [Path("/A.md")]


def test_reload_disk_text_marks_dirty_when_disk_diverges_from_buffer() -> None:
    """If an external write differs from the in-memory text the user
    hasn't touched, the buffer becomes dirty (the user's clean copy
    no longer matches disk).  The buffer's text is kept — user
    decides whether to overwrite via Save or reload via context
    menu (the latter routes back through this same call)."""
    disk_state = {"text": "v1"}
    reg = BufferRegistry(
        read_disk=lambda _p: disk_state["text"],
        write_disk=lambda _p, _t: None,
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.set_text(Path("/A.md"), "user-edit")
    # in-memory: "user-edit"  disk_text: "v1"  is_dirty=True
    disk_state["text"] = "external-edit"

    reg.reload_disk_text(Path("/A.md"))

    # User's edits preserved; disk_text is now the new external state.
    assert reg.text(Path("/A.md")) == "user-edit"
    assert reg.is_dirty(Path("/A.md")) is True


def test_reload_disk_text_marks_buffer_deleted_when_disk_missing() -> None:
    """`reload_disk_text` swallowing `FileNotFoundError` flips the
    buffer to `deleted=True` — equivalent to a `mark_deleted` call.
    Distinguishes "external rename / delete" from "transient I/O
    error"; only the missing case becomes deleted."""

    def reader(_p: Path) -> str:
        raise FileNotFoundError("/A.md vanished")

    reg = BufferRegistry(
        read_disk=lambda _p: "v1", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")
    # swap the reader after the initial subscribe so the buffer loaded
    # cleanly with "v1" first.
    reg._read_disk = reader  # type: ignore[attr-defined]

    reg.reload_disk_text(Path("/A.md"))

    assert reg.is_deleted(Path("/A.md")) is True
    assert reg.text(Path("/A.md")) == "v1"
    assert reg.is_dirty(Path("/A.md")) is True


# ─── BR-10: rename_path moves buffer state to the new key ──────────────


def test_rename_path_moves_buffer_under_new_key_preserving_state() -> None:
    """After the file-tree disk-renames A.md → A2.md, the editor host
    must be able to fetch the same in-memory text under the new key
    without losing dirty state or the subscriber set."""
    reg = BufferRegistry(
        read_disk=lambda _p: "old", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.subscribe(Path("/A.md"), "p2")
    reg.set_text(Path("/A.md"), "edited")

    reg.rename_path(Path("/A.md"), Path("/A2.md"))

    # Old key is gone.
    assert reg.subscribers(Path("/A.md")) == frozenset()
    # New key carries everything across.
    assert reg.text(Path("/A2.md")) == "edited"
    assert reg.is_dirty(Path("/A2.md")) is True
    assert reg.subscribers(Path("/A2.md")) == frozenset({"p1", "p2"})


def test_rename_path_clears_deleted_flag() -> None:
    """If A.md was marked deleted (file gone from disk), then a
    file-tree paste re-creates it at A2.md, the host calls
    `rename_path(A, A2)`.  The new buffer must come up clean of the
    deleted flag — the disk image at A2 exists again."""
    reg = BufferRegistry(
        read_disk=lambda _p: "x", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.mark_deleted(Path("/A.md"))
    assert reg.is_deleted(Path("/A.md")) is True

    reg.rename_path(Path("/A.md"), Path("/A2.md"))

    assert reg.is_deleted(Path("/A2.md")) is False


def test_rename_path_no_op_when_old_unregistered() -> None:
    reg = BufferRegistry(
        read_disk=lambda _p: "x", write_disk=lambda _p, _t: None
    )
    # No subscribe — buffer doesn't exist at the old path.

    reg.rename_path(Path("/A.md"), Path("/A2.md"))

    assert reg.subscribers(Path("/A2.md")) == frozenset()


# ─── BR-11: subscribed_paths iterator for post-turn refresh ────────────


def test_subscribed_paths_lists_every_active_buffer() -> None:
    """Host iterates `subscribed_paths()` after the agent's turn to
    call `reload_disk_text` on each one — needs a stable snapshot
    (a tuple/list, not an internal dict view that could mutate
    mid-iteration if reload triggers a buffer drop)."""
    reg = BufferRegistry(
        read_disk=lambda _p: "x", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.subscribe(Path("/B.md"), "p1")
    reg.subscribe(Path("/B.md"), "p2")

    paths = reg.subscribed_paths()

    assert set(paths) == {Path("/A.md"), Path("/B.md")}


def test_subscribed_paths_excludes_dropped_buffers() -> None:
    reg = BufferRegistry(
        read_disk=lambda _p: "x", write_disk=lambda _p, _t: None
    )
    reg.subscribe(Path("/A.md"), "p1")
    reg.unsubscribe(Path("/A.md"), "p1")  # last subscriber → buffer dropped

    assert reg.subscribed_paths() == ()
