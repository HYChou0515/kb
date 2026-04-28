"""Sign DTOs — request shape for the /rca-report/{id}/sign action.

Verification feature (Phase B). Manager (or senior / author) elevates an
RCAReport's verification_status; the /sign action validates role-vs-status
permissions in adapter/out/autocrud/actions/report.py.
"""

from __future__ import annotations

import msgspec

from rca.domain.types import SignerRole, VerificationStatus


class SignReportRequest(msgspec.Struct):
    role: SignerRole
    status: VerificationStatus
    signed_by: str
    comment: str | None = None
