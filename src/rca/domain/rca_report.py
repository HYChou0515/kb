"""RCAReport domain struct — co-authored markdown report agreed at step 9."""

from __future__ import annotations

from typing import Annotated

from autocrud import Ref
from msgspec import Struct

from rca.domain.types import SignerRole, VerificationStatus


class RCAReport(Struct):
    """The co-authored markdown report agreed at step 9.

    `agreed=True` means the author has explicitly signed off — gates entry
    into the cognee mirror. `verification_status` layers organizational
    trust on top, set via the /sign action by a manager (or senior). The
    status semantically reflects manager-signoff consensus, NOT physical
    experimental validation.
    """

    case_study_id: Annotated[str, Ref("case-study")]
    session_id: Annotated[str, Ref("session")]
    markdown_content: str = ""
    agreed: bool = False
    agreed_at: str | None = None
    signed_off_by: str = ""

    verification_status: VerificationStatus = "unverified"
    verified_by: str = ""
    verified_at: str | None = None
    verifier_role: SignerRole | None = None
    signoff_turnaround_seconds: int | None = None
    signoff_comment: str | None = None
