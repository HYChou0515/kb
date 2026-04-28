"""Custom AutoCRUD actions for Session lifecycle (open / close / abandon).

Mimics the v2 architecture's pod + PV pattern. The "PV" is the
`workspace_archive` Binary blob on the CaseStudy resource (versioned by
AutoCRUD). The "pod's filesystem" is `active_sessions/<case>/<token>/`.

Session open:
  1. Verify CaseStudy exists.
  2. Create active_sessions/<case>/<token>/.
  3. If CaseStudy.workspace_archive present → fetch blob → untar into active dir.
  4. Return Session record (AutoCRUD saves).

Session close:
  1. Archive transcript.json (if present) to transcripts/<case>/<token>.json.
  2. tar.gz the active dir → set as Binary on CaseStudy via update()
     (creates a new CaseStudy revision; AutoCRUD stores the blob).
  3. (TODO 2b) extract knowledge from transcript → GlossaryEntry / AgentFeedback /
     DocumentSource records (mirror handler populates cognee).
  4. Delete active_sessions/<case>/<token>/.
  5. Update Session: status=closed, closed_at=now.
"""

from __future__ import annotations

import datetime as dt
import io
import logging
import shutil
import tarfile
import uuid
from pathlib import Path
from typing import Annotated

from autocrud import Ref, crud
from autocrud.types import Binary
from msgspec import structs

from kb_api.models import CaseStudy, Session

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_SESSIONS_DIR = (PROJECT_ROOT / "active_sessions").resolve()
TRANSCRIPTS_DIR = (PROJECT_ROOT / "transcripts").resolve()


# Skip files / total caps for tar archiving.
_SKIP_NAMES = {".DS_Store", ".gitkeep", "transcript.json"}
_MAX_ARCHIVE_BYTES = 50 * 1024 * 1024


def _ensure_dirs() -> None:
    for d in (ACTIVE_SESSIONS_DIR, TRANSCRIPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _is_set(value) -> bool:
    """msgspec UNSET sentinel check."""
    return isinstance(value, str) and value != ""


# ─── tar / untar helpers ────────────────────────────────────────────────────


def _tar_active_dir(active_dir: Path) -> bytes:
    """Walk active dir, build a tar.gz in-memory. Skip transcript.json &
    hidden files. Raises if archive exceeds _MAX_ARCHIVE_BYTES."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for p in sorted(active_dir.rglob("*")):
            if not p.is_file():
                continue
            if p.name in _SKIP_NAMES:
                continue
            arcname = str(p.relative_to(active_dir))
            tf.add(p, arcname=arcname)
    blob = buf.getvalue()
    if len(blob) > _MAX_ARCHIVE_BYTES:
        raise ValueError(
            f"workspace archive is {len(blob)} bytes, "
            f"exceeds limit {_MAX_ARCHIVE_BYTES}. "
            "Reduce workspace contents or raise _MAX_ARCHIVE_BYTES."
        )
    return blob


def _untar_to_dir(tar_bytes: bytes, target_dir: Path) -> int:
    """Extract a tar.gz blob into target_dir. Returns # files extracted.
    Path-traversal protection: skips any member whose resolved path escapes
    target_dir.
    """
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


# ─── case ↔ workspace blob helpers ──────────────────────────────────────────


def _load_case_workspace_bytes(case_id: str) -> bytes | None:
    """Return tar bytes from CaseStudy.workspace_archive, or None."""
    rm = crud.get_resource_manager(CaseStudy)
    resource = rm.get(case_id)
    if resource is None:
        raise ValueError(f"CaseStudy {case_id} not found")
    case = resource.data
    arch = case.workspace_archive
    if arch is None:
        return None
    file_id = getattr(arch, "file_id", None)
    if not _is_set(file_id):
        return None
    blob = rm.get_blob(file_id)
    data = getattr(blob, "data", None)
    if not isinstance(data, (bytes, bytearray)):
        logger.warning("workspace blob for case %s has no data", case_id)
        return None
    return bytes(data)


def _commit_workspace_to_case(case_id: str, tar_bytes: bytes, session_token: str) -> None:
    """Update the CaseStudy with a new workspace_archive Binary, creating a
    new revision. Preserves all other fields."""
    rm = crud.get_resource_manager(CaseStudy)
    resource = rm.get(case_id)
    if resource is None:
        raise ValueError(f"CaseStudy {case_id} not found")
    case = resource.data

    # Build a new CaseStudy with same fields + new archive.
    # Use msgspec.structs.replace to clone the struct preserving fields.
    new_archive = Binary(
        data=tar_bytes,
        content_type="application/gzip",
    )
    new_case = structs.replace(case, workspace_archive=new_archive)
    rm.update(case_id, new_case)
    logger.info(
        "CaseStudy %s workspace_archive updated (%d bytes, session=%s)",
        case_id, len(tar_bytes), session_token,
    )


# ─── open_session ───────────────────────────────────────────────────────────


@crud.create_action("session", path="/open/{case_id}", label="Open Session")
async def open_session(case_id: Annotated[str, Ref("case-study")]) -> Session:
    """Open a new session against an existing CaseStudy.

    Loads CaseStudy.workspace_archive (if any) into a fresh active dir.
    """
    _ensure_dirs()

    sess_token = uuid.uuid4().hex[:8]
    active_dir = ACTIVE_SESSIONS_DIR / case_id / sess_token
    active_dir.mkdir(parents=True, exist_ok=True)

    n_loaded = 0
    tar_bytes = _load_case_workspace_bytes(case_id)
    if tar_bytes is not None:
        n_loaded = _untar_to_dir(tar_bytes, active_dir)
        logger.info(
            "session opened: case=%s active_dir=%s (hydrated %d files)",
            case_id, active_dir, n_loaded,
        )
    else:
        logger.info(
            "session opened: case=%s active_dir=%s (fresh — no prior workspace)",
            case_id, active_dir,
        )

    return Session(
        case_study_id=case_id,
        status="active",
        opened_at=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        workspace_path=str(active_dir),
        rca_completed=False,
        notes=f"hydrated {n_loaded} files from CaseStudy.workspace_archive"
        if n_loaded
        else "fresh session (no prior commits)",
    )


# ─── close_session ──────────────────────────────────────────────────────────


@crud.update_action("session", label="Close Session")
async def close_session(existing: Session) -> Session:
    """Tar the active dir → CaseStudy.workspace_archive (new revision).
    Archive transcript separately. Tear down the active dir.

    Note: knowledge extraction from transcript (GlossaryEntry / AgentFeedback /
    DocumentSource) is left as TODO until OpenCode integration lands.
    """
    _ensure_dirs()

    if existing.status != "active":
        raise ValueError(f"Cannot close session in status={existing.status!r}")
    if not existing.workspace_path:
        raise ValueError("Session has no workspace_path")

    active_dir = Path(existing.workspace_path)
    if not active_dir.exists():
        raise ValueError(f"Active dir not found: {active_dir}")

    case_id = existing.case_study_id
    sess_token = active_dir.name

    # 1. Archive transcript.json (audit copy outside the workspace tar).
    transcript_in_active = active_dir / "transcript.json"
    transcript_path: str | None = None
    if transcript_in_active.exists():
        case_transcripts = TRANSCRIPTS_DIR / case_id
        case_transcripts.mkdir(parents=True, exist_ok=True)
        out = case_transcripts / f"{sess_token}.json"
        shutil.copy2(transcript_in_active, out)
        transcript_path = str(out)
        logger.info("transcript archived: %s → %s", transcript_in_active, out)

    # 2. Tar the active dir, commit to CaseStudy as a new revision.
    tar_bytes = _tar_active_dir(active_dir)
    _commit_workspace_to_case(case_id, tar_bytes, sess_token)

    # 3. TODO(stage 2b): if transcript_path, run extractor → glossary/feedback/doc records

    # 4. Tear down the pod's filesystem.
    shutil.rmtree(active_dir)
    logger.info("active dir removed: %s", active_dir)

    # 5. Mutate the Session record we'll return.
    existing.status = "closed"
    existing.closed_at = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    if transcript_path:
        existing.transcript_path = transcript_path
    return existing


# ─── abandon_session ────────────────────────────────────────────────────────


@crud.update_action("session", label="Abandon Session")
async def abandon_session(existing: Session) -> Session:
    """Delete the active workspace WITHOUT committing back. Leaves
    CaseStudy.workspace_archive at its previous revision."""
    _ensure_dirs()

    if existing.status != "active":
        raise ValueError(f"Cannot abandon session in status={existing.status!r}")

    active_dir = Path(existing.workspace_path) if existing.workspace_path else None
    if active_dir and active_dir.exists():
        shutil.rmtree(active_dir)
        logger.info("session abandoned, active dir removed: %s", active_dir)

    existing.status = "abandoned"
    existing.closed_at = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return existing
