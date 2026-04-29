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
)
from rca.ports.out.autocrud import IAutoCrudWrapper
from rca.ports.out.graph import IGraphAdapter
from rca.services.extraction import IExtractionService
from rca.services.ingestion import IIngestionService
from rca.services.kb import KBService
from rca.services.reasoning import IReasoningService


class _FakeReasoning(IReasoningService):
    """Minimal IReasoningService fake — returns canned snippets so we can
    assert the filtering + dispatching contract of KBService.recall."""

    def __init__(self, snippets: list[str]) -> None:
        self._snippets = snippets

    async def retrieve_context(
        self, correlation: str, process_context: str | None, *, top_k: int = 12
    ) -> list[str]:
        return list(self._snippets)

    async def assess(
        self, correlation: str, *, process_context: str | None = None, top_k: int = 12
    ) -> CausalAssessment:
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
    "source_filter,must_include,must_exclude",
    [
        ("rca_reports", "rca_reports", "rca_literature"),
        ("conversations", "rca_conversations", "rca_literature"),
        ("literature", "rca_literature", "rca_reports"),
    ],
)
async def test_recall_source_filter_narrows(
    source_filter: SourceFilter, must_include: str, must_exclude: str
) -> None:
    """source_filter narrows recall results by provenance marker baked into
    the rendered snippet text. Three named tiers: rca_reports, conversations
    (rca_conversations), literature (everything else).

    "all" returns unfiltered — that's the default and not under test here."""
    snippets = [
        "Report content\n*node_set: rca_reports*",
        "Conversation content\n*node_set: rca_conversations*",
        "Literature content\n*node_set: rca_literature*",
    ]
    kb = _kb_service(_FakeReasoning(snippets))

    resp = await kb.recall(
        RecallRequest(query="x", mode="snippets", source_filter=source_filter)
    )
    assert isinstance(resp, RecallSnippetsResponse)
    assert any(must_include in s for s in resp.snippets), (
        f"expected snippet containing {must_include!r} after source_filter={source_filter}"
    )
    assert not any(must_exclude in s for s in resp.snippets), (
        f"snippet containing {must_exclude!r} should have been filtered out"
    )
