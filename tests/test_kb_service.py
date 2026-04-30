"""KBService — application-service orchestration contract.

Tests focus on the filtering + dispatching logic that lives in KBService
itself (not in the underlying ingestion / reasoning services). Fakes
substitute for the dependent ports so the test runs without LLM keys,
real cognee, or real AutoCRUD.
"""

from __future__ import annotations

from typing import cast

import pytest

from rca.ports.in_.recall import (
    CausalAssessment,
    RecallRequest,
    RecallSnippetsResponse,
    SourceFilter,
    TierFilter,
)
from rca.ports.out.autocrud import IAutoCrudWrapper
from rca.ports.out.graph import IGraphAdapter
from rca.services.extraction import IExtractionService
from rca.services.ingestion import IIngestionService
from rca.services.kb import KBService
from rca.services.reasoning import IReasoningService


class _FakeReasoning(IReasoningService):
    """Minimal IReasoningService fake — returns canned snippets so we can
    assert the filtering + dispatching contract of KBService.recall.

    Captures the last `node_set` it was called with so tests can assert
    KBService translated source_filter → node_set correctly (the load-bearing
    contract after the post-fetch substring filter was retired)."""

    def __init__(self, snippets: list[str]) -> None:
        self._snippets = snippets
        self.last_node_set: list[str] | None = None
        self.last_top_k: int | None = None

    async def retrieve_context(
        self,
        correlation: str,
        process_context: str | None,
        *,
        top_k: int = 12,
        node_set: list[str] | None = None,
    ) -> list[str]:
        self.last_node_set = node_set
        self.last_top_k = top_k
        return list(self._snippets)

    async def assess(
        self,
        correlation: str,
        *,
        process_context: str | None = None,
        top_k: int = 12,
        node_set: list[str] | None = None,
    ) -> CausalAssessment:
        self.last_node_set = node_set
        self.last_top_k = top_k
        return CausalAssessment(
            correlation=correlation,
            process_context=process_context,
            verdict="uncertain",
            verdict_reasoning="(fake)",
        )


def _kb_service(reasoning: _FakeReasoning) -> KBService:
    """KBService with only `reasoning` real; the rest are stubs not exercised
    in /recall mode=snippets. `cast(..., None)` placates type checkers
    without instantiating real (heavy) services."""
    return KBService(
        ingestion=cast(IIngestionService, None),
        reasoning=reasoning,
        extraction=cast(IExtractionService, None),
        autocrud=cast(IAutoCrudWrapper, None),
        graph=cast(IGraphAdapter, None),
    )


async def test_recall_exclude_refuted_drops_refuted_snippets() -> None:
    """When exclude_refuted=True, the recall service drops any snippet whose
    rendered text carries the rca_reports_refuted provenance tag — useful for
    a caller that only wants positive knowledge, never ruled-out hypotheses.

    Default is False: refuted IS returned, so the reasoner sees it and applies
    the special-case rule from the system prompt."""
    snippets = [
        "Mechanism: CMP slurry pH drift causes Cu dishing\n*node_set: rca_reports_verified*",
        "Earlier case rejected this hypothesis\n*node_set: rca_reports_refuted*",
        "Background literature on dishing\n*node_set: rca_literature*",
    ]
    kb = _kb_service(_FakeReasoning(snippets))

    # default — refuted included
    resp = await kb.recall(RecallRequest(query="Cu dishing", mode="snippets"))
    assert isinstance(resp, RecallSnippetsResponse)
    assert any("rca_reports_refuted" in s for s in resp.snippets), (
        "refuted snippet must be included by default"
    )

    # exclude_refuted=True — refuted dropped
    resp_filtered = await kb.recall(
        RecallRequest(query="Cu dishing", mode="snippets", exclude_refuted=True)
    )
    assert isinstance(resp_filtered, RecallSnippetsResponse)
    assert not any("rca_reports_refuted" in s for s in resp_filtered.snippets), (
        "refuted snippet must be filtered out"
    )
    # Verified + literature survive
    assert any("rca_reports_verified" in s for s in resp_filtered.snippets)
    assert any("rca_literature" in s for s in resp_filtered.snippets)


@pytest.mark.parametrize(
    "source_filter,expected_node_set",
    [
        ("all", None),
        ("rca_reports", ["rca_reports"]),
        ("conversations", ["rca_conversations"]),
        ("literature", ["rca_literature"]),
    ],
)
async def test_recall_source_filter_pushes_down_to_node_set(
    source_filter: SourceFilter, expected_node_set: list[str] | None
) -> None:
    """source_filter is now enforced at the graph layer via cognee's NodeSet
    matcher (passed through reasoning.retrieve_context as node_set). KBService's
    job is the translation; the actual filter happens upstream.

    "all" → None means "no filter applied" — cognee returns from any tag."""
    fake = _FakeReasoning(["irrelevant"])
    kb = _kb_service(fake)

    await kb.recall(
        RecallRequest(query="x", mode="snippets", source_filter=source_filter)
    )

    assert fake.last_node_set == expected_node_set, (
        f"source_filter={source_filter} should push down node_set={expected_node_set} "
        f"to reasoning, got {fake.last_node_set}"
    )


@pytest.mark.parametrize(
    "tier_filter,expected_node_set",
    [
        ("any", None),
        ("verified", ["rca_reports_verified"]),
        ("verified_or_partial", ["rca_reports_verified", "rca_reports_partial"]),
    ],
)
async def test_recall_tier_filter_pushes_down_to_node_set(
    tier_filter: TierFilter, expected_node_set: list[str] | None
) -> None:
    """tier_filter narrows to manager-signoff'd RCA report tiers via node_set
    push-down. "any" means no constraint (delegates to source_filter).
    "verified" / "verified_or_partial" map to the corresponding rca_reports_<tier>
    cognee node_set tags."""
    fake = _FakeReasoning(["irrelevant"])
    kb = _kb_service(fake)

    await kb.recall(RecallRequest(query="x", mode="snippets", tier_filter=tier_filter))

    assert fake.last_node_set == expected_node_set


async def test_tier_filter_overrides_source_filter() -> None:
    """tier_filter is RCA-report-specific; when set, it overrides source_filter
    rather than producing the semantically incoherent "verified conversations"
    intersection. Caller-friendly behavior — least surprise."""
    fake = _FakeReasoning(["irrelevant"])
    kb = _kb_service(fake)

    await kb.recall(
        RecallRequest(
            query="x",
            mode="snippets",
            source_filter="conversations",  # would normally narrow to rca_conversations
            tier_filter="verified",  # but this overrides
        )
    )

    assert fake.last_node_set == ["rca_reports_verified"], (
        "tier_filter should override source_filter — not produce intersection"
    )


async def test_assessment_mode_also_applies_node_set_filter() -> None:
    """assessment mode previously ignored source_filter / tier_filter — only
    snippets mode honored them. Now both modes push the filter down to
    reasoning, so an assessment based on verified-only context can be
    requested via tier_filter='verified'."""
    fake = _FakeReasoning(["irrelevant"])
    kb = _kb_service(fake)

    await kb.recall(
        RecallRequest(
            query="x",
            mode="assessment",
            tier_filter="verified",
        )
    )

    assert fake.last_node_set == ["rca_reports_verified"], (
        "assessment mode must also push tier_filter down to reasoning.assess"
    )


async def test_recall_top_k_no_longer_eaten_by_source_filter() -> None:
    """Regression: the old post-fetch substring filter ran AFTER reasoning
    returned top_k items, so a narrow source_filter could shrink the response
    far below the requested top_k. With node_set push-down, cognee returns
    top_k items already matching the filter — the requested top_k actually
    gets returned (modulo exclude_refuted, which is still a post-filter)."""
    snippets = [f"snippet-{i}\n*node_set: rca_reports*" for i in range(5)]
    fake = _FakeReasoning(snippets)
    kb = _kb_service(fake)

    resp = await kb.recall(
        RecallRequest(query="x", mode="snippets", source_filter="rca_reports", top_k=5)
    )
    assert isinstance(resp, RecallSnippetsResponse)
    assert len(resp.snippets) == 5, (
        "top_k=5 with matching source_filter should return all 5 — old code "
        "could shrink this if filter happened post-fetch"
    )
