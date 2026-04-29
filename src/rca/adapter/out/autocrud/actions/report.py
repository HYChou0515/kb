"""RCAReport actions — sign_report (manager-signoff trust elevation).

Plain async function; registered at runtime in
AutoCrudWrapper.register_actions(). Implements the verification feature:
manager elevates verification_status from default `unverified` to
`partial` / `verified`, or any role marks `refuted` (with a comment).

Status semantics: `verified` ≡ "manager-signed at top tier", NOT a
claim of physical experimental validation. The reasoner system prompt
makes this explicit when consuming the resulting node_set tags.
"""

import datetime as dt
import logging

from rca.domain.rca_report import RCAReport
from rca.domain.types import SignerRole, VerificationStatus
from rca.ports.in_.sign import SignReportRequest

logger = logging.getLogger(__name__)


_ROLE_ALLOWS: dict[SignerRole, set[VerificationStatus]] = {
    "author": {"unverified", "refuted"},
    "senior": {"unverified", "partial", "refuted"},
    "manager": {"unverified", "partial", "verified", "refuted"},
}


async def sign_report(existing: RCAReport, payload: SignReportRequest) -> RCAReport:
    """Elevate (or downgrade) an RCAReport's verification_status.

    Validation:
      - Report must already be agreed=True (author signoff is prerequisite)
      - role-vs-status permissions per _ROLE_ALLOWS
      - refuted requires non-empty comment

    Side effect: cognee mirror re-runs on the AutoCRUD AfterUpdate event,
    re-rendering the report under the new status's node_set tag (e.g.
    rca_reports_verified). Old chunk under the previous tag remains in
    cognee until v2 implements chunk-level lifecycle tracking.
    """
    if not existing.agreed:
        raise ValueError("cannot sign an unagreed (draft) report")
    if payload.status not in _ROLE_ALLOWS[payload.role]:
        raise ValueError(f"role={payload.role!r} cannot set status={payload.status!r}")
    if payload.status == "refuted" and not (
        payload.comment and payload.comment.strip()
    ):
        raise ValueError("refuted status requires a non-empty comment")

    now = dt.datetime.now(dt.UTC)
    turnaround: int | None = None
    if existing.agreed_at:
        try:
            # fromisoformat() in Python 3.11+ accepts a trailing 'Z'.
            # Force UTC if the parsed value happened to be naive.
            agreed_dt = dt.datetime.fromisoformat(existing.agreed_at)
            if agreed_dt.tzinfo is None:
                agreed_dt = agreed_dt.replace(tzinfo=dt.UTC)
            turnaround = int((now - agreed_dt).total_seconds())
        except ValueError:
            pass

    existing.verification_status = payload.status
    existing.verifier_role = payload.role
    existing.verified_by = payload.signed_by
    existing.verified_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    existing.signoff_turnaround_seconds = turnaround
    existing.signoff_comment = payload.comment
    return existing
