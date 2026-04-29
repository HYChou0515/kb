"""Sign DTOs — request shape for the /rca-report/{id}/sign action.

Verification feature (Phase B). Manager (or senior / author) elevates an
RCAReport's verification_status; the /sign action validates role-vs-status
permissions in adapter/out/autocrud/actions/report.py.

Pydantic BaseModel (not msgspec.Struct) so FastAPI's request body parser
treats it as a single body payload instead of breaking each field into
query parameters.
"""

from pydantic import BaseModel

from rca.domain.types import SignerRole, VerificationStatus


class SignReportRequest(BaseModel):
    role: SignerRole
    status: VerificationStatus
    signed_by: str
    comment: str | None = None
