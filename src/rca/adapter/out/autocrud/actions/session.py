"""Session lifecycle actions — open / close / abandon.

Plain async functions (no decorators); registered at runtime in
AutoCrudWrapper.register_actions(). Each is built via a factory that
captures the case_study_mgr accessor so the action body can reach
the workspace blob without importing the AutoCRUD singleton.

Mimics the v2 architecture's pod + PV pattern. The "PV" is the
`workspace_archive` Binary blob on the CaseStudy resource (versioned by
AutoCRUD). The "pod's filesystem" is `active_sessions/<case>/<token>/`.
"""

import datetime as dt
import io
import logging
import shutil
import tarfile
import uuid
from pathlib import Path
from typing import Annotated, Any, Callable

from autocrud import Ref
from autocrud.types import Binary
from msgspec import structs

from rca.domain.session import Session

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ACTIVE_SESSIONS_DIR = (PROJECT_ROOT / "active_sessions").resolve()
TRANSCRIPTS_DIR = (PROJECT_ROOT / "transcripts").resolve()


_SKIP_NAMES = {".DS_Store", ".gitkeep", "transcript.json"}
_MAX_ARCHIVE_BYTES = 50 * 1024 * 1024


def _ensure_dirs() -> None:
    for d in (ACTIVE_SESSIONS_DIR, TRANSCRIPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _is_set(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _tar_active_dir(active_dir: Path) -> bytes:
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
            f"exceeds limit {_MAX_ARCHIVE_BYTES}."
        )
    return blob


def _untar_to_dir(tar_bytes: bytes, target_dir: Path) -> int:
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


def make_session_actions(case_study_mgr_factory: Callable[[], Any]):
    """Build the session lifecycle action functions bound to a CaseStudy
    resource manager accessor. The accessor returns the manager every
    invocation (so it can be re-resolved if the underlying AutoCRUD
    instance changes — e.g. test fixtures).
    """

    def _load_case_workspace_bytes(case_id: str) -> bytes | None:
        rm = case_study_mgr_factory()
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
        rm = case_study_mgr_factory()
        resource = rm.get(case_id)
        if resource is None:
            raise ValueError(f"CaseStudy {case_id} not found")
        case = resource.data
        new_archive = Binary(
            data=tar_bytes,
            content_type="application/gzip",
        )
        new_case = structs.replace(case, workspace_archive=new_archive)
        # AutoCRUD per-request ContextVars (now_ctx/user_ctx) are scoped to the
        # CURRENT resource's manager. When the Session action updates a
        # different resource (CaseStudy), that resource's ContextVars aren't
        # set. Bridge them explicitly with autocrud's Ctx.ctx() helper.
        with rm.user_ctx.ctx("system"), rm.now_ctx.ctx(dt.datetime.utcnow()):
            rm.update(case_id, new_case)
        logger.info(
            "CaseStudy %s workspace_archive updated (%d bytes, session=%s)",
            case_id, len(tar_bytes), session_token,
        )

    async def open_session(case_id: Annotated[str, Ref("case-study")]) -> Session:
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

    async def close_session(existing: Session) -> Session:
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

        transcript_in_active = active_dir / "transcript.json"
        transcript_path: str | None = None
        if transcript_in_active.exists():
            case_transcripts = TRANSCRIPTS_DIR / case_id
            case_transcripts.mkdir(parents=True, exist_ok=True)
            out = case_transcripts / f"{sess_token}.json"
            shutil.copy2(transcript_in_active, out)
            transcript_path = str(out)
            logger.info("transcript archived: %s → %s", transcript_in_active, out)

        tar_bytes = _tar_active_dir(active_dir)
        _commit_workspace_to_case(case_id, tar_bytes, sess_token)

        shutil.rmtree(active_dir)
        logger.info("active dir removed: %s", active_dir)

        existing.status = "closed"
        existing.closed_at = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        if transcript_path:
            existing.transcript_path = transcript_path
        return existing

    async def abandon_session(existing: Session) -> Session:
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

    return open_session, close_session, abandon_session
