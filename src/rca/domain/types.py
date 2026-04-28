"""Shared Literal aliases for domain structs (DB-persisted types only)."""

from __future__ import annotations

from typing import Literal

CaseStatus = Literal["active", "closed", "archived"]
SessionStatus = Literal["active", "closed", "abandoned"]
GlossaryConfidence = Literal["expert_explicit", "expert_implicit", "guessed"]
FeedbackType = Literal["correction", "confirmation", "clarification"]

DocumentKind = Literal[
    "literature",
    "primer",
    "rca_report_md",
    "conversation_extracted",
]

# Verification feature (Phase B). Defined here so Phase A schema migrations
# pre-allocate the column even if no records carry non-default values yet.
VerificationStatus = Literal["unverified", "partial", "verified", "refuted"]
SignerRole = Literal["author", "senior", "manager"]
