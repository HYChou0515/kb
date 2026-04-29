"""Verification feature — sign_report action contract.

Tests describe the role/status permission policy and validation rules,
not the AutoCRUD plumbing. The action is a plain async function so we
call it directly with a freshly-constructed RCAReport + SignReportRequest.
"""

from __future__ import annotations

import pytest

from rca.adapter.out.autocrud.actions.report import sign_report
from rca.domain.rca_report import RCAReport
from rca.ports.in_.sign import SignReportRequest


def _agreed_report(agreed_at: str = "2020-01-01T00:00:00Z") -> RCAReport:
    return RCAReport(
        case_study_id="c1",
        session_id="s1",
        markdown_content="# test",
        agreed=True,
        agreed_at=agreed_at,
        signed_off_by="alice",
    )


async def test_sign_rejects_draft() -> None:
    """An unagreed (draft) report cannot be signed at any tier — author
    signoff (agreed=True) is the prerequisite to ANY verification status."""
    draft = RCAReport(case_study_id="c1", session_id="s1", agreed=False)
    payload = SignReportRequest(role="manager", status="verified", signed_by="alice")
    with pytest.raises(ValueError, match="unagreed"):
        await sign_report(draft, payload)


@pytest.mark.parametrize(
    "role,status",
    [
        ("author", "partial"),
        ("author", "verified"),
        ("senior", "verified"),
    ],
)
async def test_sign_rejects_role_status_overreach(role: str, status: str) -> None:
    """Role/status policy: author may only set unverified|refuted; senior may
    only set unverified|partial|refuted; verified is manager-only.

    Locks the political contract: "verified" ≡ manager-signed at top tier.
    A senior or author cannot self-elevate past their tier.
    """
    report = _agreed_report()
    payload = SignReportRequest(role=role, status=status, signed_by="bob")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot set status"):
        await sign_report(report, payload)


@pytest.mark.parametrize("comment", [None, "", "   "])
async def test_sign_refuted_requires_nonempty_comment(comment: str | None) -> None:
    """Refuted is the one status that demands an explanation — refuting a case
    without saying why corrupts the KB (future readers can't tell whether the
    mechanism was bogus or just inapplicable to this case)."""
    report = _agreed_report()
    payload = SignReportRequest(
        role="manager", status="refuted", signed_by="bob", comment=comment
    )
    with pytest.raises(ValueError, match="refuted.*comment"):
        await sign_report(report, payload)


async def test_sign_success_writes_verification_fields() -> None:
    """Manager-signed verified path: status, role, who, when, comment, and
    turnaround are all set. Turnaround is `verified_at - agreed_at` in seconds —
    the rubber-stamp signal (very short turnaround on a long report = manager
    didn't actually read it)."""
    report = _agreed_report()
    payload = SignReportRequest(
        role="manager",
        status="verified",
        signed_by="alice",
        comment="reviewed at design review meeting",
    )

    result = await sign_report(report, payload)

    assert result.verification_status == "verified"
    assert result.verifier_role == "manager"
    assert result.verified_by == "alice"
    assert result.signoff_comment == "reviewed at design review meeting"
    assert result.verified_at is not None and result.verified_at.endswith("Z")
    assert result.signoff_turnaround_seconds is not None
    assert result.signoff_turnaround_seconds >= 0
