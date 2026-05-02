"""Session lifecycle action helpers — file/tar utilities only.

The action methods (open_session / close_session / abandon_session) live
on AutoCrudWrapper as bound methods so type checkers can resolve their
signatures cleanly (no factory closure tuple). The helpers below are
plain module-level functions used by those methods.

Mimics the v2 architecture's pod + PV pattern. The "PV" is the
`workspace_archive` Binary blob on the CaseStudy resource (versioned by
AutoCRUD). The "pod's filesystem" is `active_sessions/<case>/<token>/`.
"""

import io
import logging
import tarfile
from pathlib import Path
from typing import Any, TypeGuard

logger = logging.getLogger(__name__)


# __file__: <project>/src/rca/adapter/out/autocrud/actions/session.py — climb
# 6 levels (actions → autocrud → out → adapter → rca → src) to project root.
PROJECT_ROOT = Path(__file__).resolve().parents[6]
ACTIVE_SESSIONS_DIR = (PROJECT_ROOT / "active_sessions").resolve()
TRANSCRIPTS_DIR = (PROJECT_ROOT / "transcripts").resolve()


SKIP_NAMES = {".DS_Store", ".gitkeep", "transcript.json"}
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024


def ensure_dirs() -> None:
    for d in (ACTIVE_SESSIONS_DIR, TRANSCRIPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def is_set(value: Any) -> TypeGuard[str]:
    """TypeGuard so static checkers narrow `Any | None` → `str` after this check."""
    return isinstance(value, str) and value != ""


def tar_active_dir(active_dir: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for p in sorted(active_dir.rglob("*")):
            if not p.is_file():
                continue
            if p.name in SKIP_NAMES:
                continue
            arcname = str(p.relative_to(active_dir))
            tf.add(p, arcname=arcname)
    blob = buf.getvalue()
    if len(blob) > MAX_ARCHIVE_BYTES:
        raise ValueError(
            f"workspace archive is {len(blob)} bytes, "
            f"exceeds limit {MAX_ARCHIVE_BYTES}."
        )
    return blob


def untar_to_dir(tar_bytes: bytes, target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_resolved = target_dir.resolve()
    n = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tf:
        for member in tf.getmembers():
            if not (member.isfile() or member.isdir()):
                continue
            candidate = (target_dir / member.name).resolve()
            try:
                candidate.relative_to(target_resolved)
            except ValueError:
                logger.warning("skipping path-traversal: %s", member.name)
                continue
            tf.extract(member, target_dir)
            if member.isfile():
                n += 1
    return n
