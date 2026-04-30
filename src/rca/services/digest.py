"""digest — session conversation digest to cognee.

digest_session(session_id, autocrud) extracts the session transcript (if any)
and creates a DocumentSource(source_kind="conversation_extracted") record.
The CogneeMirrorHandler fires on the AutoCRUD create event and ingests the
text into cognee (node_set="rca_conversations").

Dedup guard: Session.digested_at is set after successful digest. Subsequent
calls are no-ops so finalize + manual re-trigger don't double-ingest.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

from rca.domain.document import DocumentSource
from rca.ports.out.autocrud import IAutoCrudWrapper

logger = logging.getLogger(__name__)


async def digest_session(
    session_id: str,
    *,
    autocrud: IAutoCrudWrapper,
) -> bool:
    """Ingest the session transcript into cognee via AutoCRUD DocumentSource.

    Returns True if digest was performed, False if already digested or no
    transcript available.

    Raises ResourceIDNotFoundError if session_id does not exist.
    """
    session_rm = autocrud.session_mgr()
    session_resource = session_rm.get(session_id)
    sess = session_resource.data

    if sess.digested_at:
        logger.debug(
            "session %s already digested at %s — skipping", session_id, sess.digested_at
        )
        return False

    transcript_text = _read_transcript(sess.transcript_path)
    if not transcript_text:
        logger.info("session %s has no transcript — skipping digest", session_id)
        return False

    now = dt.datetime.now(dt.UTC)
    doc = DocumentSource(
        label=f"Conversation — session {session_id}",
        source_kind="conversation_extracted",
        text=transcript_text,
        case_study_id=sess.case_study_id or None,
        session_id=session_id,
    )
    doc_rm = autocrud.document_mgr()
    doc_rm.create(doc, user="system", now=now)

    # Mark the session as digested so this won't be re-run.
    sess.digested_at = now.isoformat()
    session_rm.update(session_id, sess, user="system", now=now)

    logger.info(
        "session digested: session=%s case=%s transcript_chars=%d",
        session_id,
        sess.case_study_id,
        len(transcript_text),
    )
    return True


# ─── helpers ─────────────────────────────────────────────────────────────────


def _read_transcript(transcript_path: str | None) -> str:
    """Read transcript text from disk. Returns empty string if not available."""
    if not transcript_path:
        return ""
    path = Path(transcript_path)
    if not path.exists():
        logger.warning("transcript path not found: %s", path)
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("could not read transcript %s: %s", path, exc)
        return ""
