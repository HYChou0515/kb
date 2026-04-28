"""RCAReport actions — sign_report (manager-signoff trust elevation).

Plain async function; registered at runtime in
AutoCrudWrapper.register_actions(). Implements the verification feature:
manager elevates verification_status from default `unverified` to
`partial` / `verified`, or any role marks `refuted` (with a comment).

Status semantics: `verified` ≡ "manager-signed at top tier", NOT a
claim of physical experimental validation. The reasoner system prompt
makes this explicit when consuming the resulting node_set tags.
"""

from __future__ import annotations

import datetime as dt
import logging

from rca.domain.rca_report import RCAReport
from rca.domain.types import SignerRole, VerificationStatus

logger = logging.getLogger(__name__)


_ROLE_ALLOWS: dict[SignerRole, set[VerificationStatus]] = {
    "author":  {"unverified", "refuted"},
    "senior":  {"unverified", "partial", "refuted"},
    "manager": {"unverified", "partial", "verified", "refuted"},
}


async def sign_report(
    existing: RCAReport,
    role: SignerRole,
    status: VerificationStatus,
    signed_by: str,
    comment: str | None = None,
) -> RCAReport:
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
    if status not in _ROLE_ALLOWS[role]:
        raise ValueError(f"role={role!r} cannot set status={status!r}")
    if status == "refuted" and not (comment and comment.strip()):
        raise ValueError("refuted status requires a non-empty comment")

    now = dt.datetime.utcnow()
    turnaround: int | None = None
    if existing.agreed_at:
        try:
            agreed_dt = dt.datetime.fromisoformat(existing.agreed_at.rstrip("Z"))
            turnaround = int((now - agreed_dt).total_seconds())
        except ValueError:
            pass

    existing.verification_status = status
    existing.verifier_role = role
    existing.verified_by = signed_by
    existing.verified_at = now.isoformat(timespec="seconds") + "Z"
    existing.signoff_turnaround_seconds = turnaround
    existing.signoff_comment = comment
    return existing
