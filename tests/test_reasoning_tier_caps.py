"""Reasoner output tier-aware confidence post-validation.

The trust hierarchy lives in two places today:
  1. The system prompt tells the LLM to weight by tier (decorative — no
     enforcement; LLM may ignore).
  2. The /recall input can be filtered via tier_filter so reasoner only sees
     trusted snippets (input-side guard).

This test file covers the OUTPUT-side guard: even when the caller doesn't
filter (default), the reasoner's MechanismHypothesis.confidence must reflect
what the supporting snippets actually support.

Concretely: if no snippet carries a verified or partial tag, no mechanism
should claim confidence="high" — that would be the false-alarm pattern the
POC explicitly exists to prevent (high-confidence claim built on unverified
or literature evidence alone).

Tests the post-validator as a pure function (`_apply_tier_caps(assessment,
snippets) → assessment`). The full assess() integration is exercised by
integration tests; this file isolates the rule logic.
"""

from __future__ import annotations

from typing import Literal

from rca.ports.in_.recall import (
    CausalAssessment,
    MechanismHypothesis,
)
from rca.services.reasoning import _apply_tier_caps

Confidence = Literal["high", "medium", "low"]


def _assessment(
    *,
    mechanism_confidence: Confidence = "high",
    snippets: list[str] | None = None,
) -> CausalAssessment:
    return CausalAssessment(
        correlation="X correlates with Y",
        process_context=None,
        verdict="plausible",
        verdict_reasoning="r",
        mechanisms=[
            MechanismHypothesis(
                description="A → B via mechanism",
                supporting_entities=["entity-1"],
                confidence=mechanism_confidence,
                citations=["snippet-1"],
            )
        ],
        confounders=[],
        suggested_investigations=[],
        knowledge_gaps=[],
        raw_context_snippets=snippets or [],
    )


def test_high_confidence_capped_to_medium_when_no_verified_signal() -> None:
    """If the entire snippet pool lacks any verified/partial tier signal, no
    mechanism may claim confidence="high" — that's the false-alarm pattern.
    The cap is "medium", not "low", because literature/conversations are still
    legitimate priors; just not strong enough for "high"."""
    snippets = [
        "Background on CMP slurry chemistry\n*node_set: rca_literature*",
        "Tribal knowledge from a recent discussion\n*node_set: rca_conversations*",
    ]
    asm = _assessment(mechanism_confidence="high", snippets=snippets)

    capped = _apply_tier_caps(asm, snippets)

    assert capped.mechanisms[0].confidence == "medium", (
        "high confidence with no verified/partial citations must be capped"
    )


def test_high_confidence_preserved_when_verified_signal_present() -> None:
    """When the snippet pool DOES contain at least one verified-tier RCA report,
    a mechanism's high confidence is legitimate — don't downgrade. Verified
    means manager-signoff'd organizational consensus on the original case;
    that's the strongest available evidence the system can cite."""
    snippets = [
        "Background prior\n*node_set: rca_literature*",
        (
            "# RCA Report (verified)\n"
            "*case_study_id: c1 | session_id: s1 | "
            "verification_status: verified | verified_by: manager-bob*\n"
            "Cu barrier thinning at via M2 confirmed by FIB-SEM."
        ),
    ]
    asm = _assessment(mechanism_confidence="high", snippets=snippets)

    capped = _apply_tier_caps(asm, snippets)

    assert capped.mechanisms[0].confidence == "high", (
        "verified tier signal in pool — high confidence is legitimate, no cap"
    )


def test_partial_tier_also_unlocks_high_confidence() -> None:
    """Partial = manager-signed-with-reservations. Still strong enough to
    legitimize a high-confidence mechanism per the trust hierarchy."""
    snippets = [
        (
            "# RCA Report (partial)\n"
            "*verification_status: partial | verified_by: manager-bob*\n"
            "Tungsten drift observed; one of two candidate causes ruled out."
        ),
    ]
    asm = _assessment(mechanism_confidence="high", snippets=snippets)

    capped = _apply_tier_caps(asm, snippets)

    assert capped.mechanisms[0].confidence == "high"


def test_lower_confidences_never_promoted() -> None:
    """The post-validator only DOWNGRADES — it must never upgrade a "low" or
    "medium" claim, even when verified evidence exists. The LLM's lower
    confidence is its judgment call about THIS specific mechanism's strength
    of evidence; we only enforce the upper bound."""
    snippets = [
        "*verification_status: verified*\nCu dishing confirmed at process step 3"
    ]
    asm = _assessment(mechanism_confidence="low", snippets=snippets)

    capped = _apply_tier_caps(asm, snippets)

    assert capped.mechanisms[0].confidence == "low", (
        "post-validator must not promote — only cap"
    )
