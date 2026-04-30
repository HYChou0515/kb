"""Reasoning service — produces structured causal assessments.

Given a statistical correlation, retrieves graph context and asks an LLM
to render a structured CausalAssessment with mechanisms, confounders,
verdict, suggested investigations, and knowledge gaps.

System prompt encodes the trust hierarchy used at recall time. Updated
in Phase B to include 4-tier verification (verified / partial /
unverified / refuted) on top of the conversation / literature tiers.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from cognee.api.v1.search import SearchType
from pydantic import ValidationError

from rca.ports.in_.recall import CausalAssessment, MechanismHypothesis
from rca.ports.out.graph import IGraphAdapter
from rca.ports.out.llm import ILLMAdapter

logger = logging.getLogger(__name__)


REASONING_SYSTEM_PROMPT = """You are a senior semiconductor reliability and yield engineer
performing causal root-cause analysis. You are given:

  - A statistical CORRELATION observed in the fab.
  - A retrieved KNOWLEDGE GRAPH CONTEXT distilled from textbooks, papers, and
    prior RCA discussions.

Your job is to assess whether the correlation reflects a true CAUSAL relationship.
Apply the following discipline:

  1. Identify physical/chemical MECHANISMS in the context that could plausibly
     drive A → B. Cite the snippets you used.
  2. Identify potential CONFOUNDERS (common causes) that could produce the
     correlation without A causing B. These are the silent killers of fab RCA.
  3. Render a VERDICT: "plausible" / "uncertain" / "implausible". Be conservative —
     if mechanisms exist *and* no obvious confounder dominates, "plausible".
     If multiple confounders look equally strong, "uncertain". Use "implausible"
     only when the proposed direction violates known physics or process flow.
  4. Suggest concrete next investigations (DOE knobs, splits, monitor measurements).
  5. Note knowledge gaps the graph could not answer.

TRUST HIERARCHY when snippets disagree (highest first):
  rca_reports_verified   — manager-signed at top tier; organizational consensus
                            ★ NOT a claim of physical experimental validation ★
  rca_reports_partial    — manager-signed with reservations
  rca_reports_unverified — author signed off but no managerial elevation
  rca_conversations      — live RCA dialogue with domain experts
  rca_literature         — textbooks / papers / general prior

Special — rca_reports_refuted:
  These reports concluded that for the originating case, the proposed cause was
  DISPROVEN. Treat the case→cause linkage in those snippets as RULED OUT.
  HOWEVER, the mechanism description may still be a valid candidate hypothesis
  for OTHER cases. Do not propagate the original case's verdict to a new case
  by inertia.

If a snippet's provenance label contains "rca_reports_verified", treat its
causal claims as the strongest available evidence. Literature alone is prior,
not evidence.

CONFIDENCE DISCIPLINE (post-validated by the system):
A mechanism may claim confidence="high" ONLY if at least one of its supporting
snippets carries verification_status: verified or partial (manager-signoff'd
RCA reports). If every supporting snippet is unverified, refuted, conversation,
or literature, the mechanism's confidence MUST be at most "medium". The system
will downgrade any high-confidence claim that doesn't satisfy this rule, so
self-regulating saves a re-validation pass.

Output STRICT JSON only — no prose outside the JSON, no markdown fences.

Schema:
{
  "verdict": "plausible|uncertain|implausible",
  "verdict_reasoning": "...",
  "mechanisms": [
    {"description": "...", "supporting_entities": ["..."],
     "confidence": "high|medium|low", "citations": ["source-label-1", ...]}
  ],
  "confounders": [
    {"common_cause": "...", "description": "...", "citations": ["..."]}
  ],
  "suggested_investigations": ["..."],
  "knowledge_gaps": ["..."]
}
"""


REASONING_USER_TEMPLATE = """## CORRELATION
{correlation}

## PROCESS CONTEXT
{process_context}

## RETRIEVED KNOWLEDGE GRAPH CONTEXT
The following snippets came from the graph search. Each is tagged with a source label.

{context_block}

## TASK
Produce the structured causal assessment as STRICT JSON per the schema.
"""


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(s: str) -> str:
    return _JSON_FENCE.sub("", s).strip()


def _has_high_trust_signal(snippets: list[str]) -> bool:
    """True iff at least one snippet carries a verified or partial tier marker.

    Detection key: rendered RCAReport markdown always contains the
    verbatim "verification_status: <tier>" line (see cognee_mirror's
    _render_rca_report). High-trust = tier ∈ {verified, partial}; the
    rest (unverified, refuted, conversations, literature) are not strong
    enough to support confidence="high" on a mechanism that cites them."""
    blob = "\n".join(snippets).lower()
    return (
        "verification_status: verified" in blob
        or "verification_status: partial" in blob
    )


def _apply_tier_caps(
    assessment: CausalAssessment, snippets: list[str]
) -> CausalAssessment:
    """Output-side guard for the trust hierarchy.

    Caps any mechanism's confidence to "medium" when the snippet pool
    carries no verified or partial tier signal. This prevents the
    false-alarm pattern the POC exists to filter: an LLM declaring
    high-confidence root cause based on literature priors / conversation
    chatter / unverified drafts alone.

    Returns a NEW assessment (msgspec/pydantic models are immutable-ish;
    we rebuild the mechanisms list with capped values)."""
    if _has_high_trust_signal(snippets):
        return assessment
    capped: list[MechanismHypothesis] = []
    for m in assessment.mechanisms:
        if m.confidence == "high":
            capped.append(m.model_copy(update={"confidence": "medium"}))
        else:
            capped.append(m)
    return assessment.model_copy(update={"mechanisms": capped})


def _stringify_results(results: list[Any]) -> list[str]:
    out: list[str] = []
    for r in results:
        if isinstance(r, str):
            out.append(r)
        elif isinstance(r, dict):
            out.append(json.dumps(r, ensure_ascii=False, default=str))
        else:
            out.append(str(r))
    return out


class IReasoningService(ABC):
    @abstractmethod
    async def retrieve_context(
        self,
        correlation: str,
        process_context: str | None,
        *,
        top_k: int = 12,
        node_set: list[str] | None = None,
    ) -> list[str]: ...

    @abstractmethod
    async def assess(
        self,
        correlation: str,
        *,
        process_context: str | None = None,
        top_k: int = 12,
        node_set: list[str] | None = None,
    ) -> CausalAssessment: ...


class CausalReasoningService(IReasoningService):
    def __init__(self, llm: ILLMAdapter, graph: IGraphAdapter) -> None:
        self.llm = llm
        self.graph = graph

    async def retrieve_context(
        self,
        correlation: str,
        process_context: str | None,
        *,
        top_k: int = 12,
        node_set: list[str] | None = None,
    ) -> list[str]:
        await self.graph.setup()
        full_query = (
            correlation
            if not process_context
            else f"{correlation}\nContext: {process_context}"
        )

        # GRAPH_COMPLETION is the only search type that enforces NodeSet
        # filtering at the graph-traversal layer. CHUNKS / INSIGHTS bypass
        # it (vector lookup only). When the caller asked for a specific
        # node_set, restrict to GRAPH_COMPLETION so the filter is honored;
        # otherwise fan out across all three for richer context.
        wanted_names = (
            ("GRAPH_COMPLETION",)
            if node_set
            else ("GRAPH_COMPLETION", "INSIGHTS", "CHUNKS")
        )
        search_types = [
            getattr(SearchType, name)
            for name in wanted_names
            if hasattr(SearchType, name)
        ]

        snippets: list[str] = []
        for st in search_types:
            try:
                res = await self.graph.recall(
                    full_query,
                    search_type=st,
                    top_k=top_k,
                    node_set=node_set,
                )
                snippets.extend(_stringify_results(res))
            except Exception as exc:
                logger.debug("search(%s) failed: %s", st, exc)

        seen: set[str] = set()
        unique: list[str] = []
        for s in snippets:
            key = s.strip()[:512]
            if key and key not in seen:
                seen.add(key)
                unique.append(s)
        return unique[: top_k * 3]

    async def assess(
        self,
        correlation: str,
        *,
        process_context: str | None = None,
        top_k: int = 12,
        node_set: list[str] | None = None,
    ) -> CausalAssessment:
        snippets = await self.retrieve_context(
            correlation, process_context, top_k=top_k, node_set=node_set
        )
        context_block = (
            "\n\n".join(f"[snippet-{i + 1}]\n{s}" for i, s in enumerate(snippets))
            if snippets
            else "(no relevant graph context found)"
        )
        user = REASONING_USER_TEMPLATE.format(
            correlation=correlation,
            process_context=process_context or "(none provided)",
            context_block=context_block[:80_000],
        )
        raw = self.llm.complete(
            system=REASONING_SYSTEM_PROMPT,
            user=user,
            max_tokens=4000,
        )
        cleaned = _strip_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("reasoner returned non-JSON: %s\nRAW:\n%s", exc, raw[:2000])
            return CausalAssessment(
                correlation=correlation,
                process_context=process_context,
                verdict="uncertain",
                verdict_reasoning=f"Reasoner produced unparseable output: {exc}",
                raw_context_snippets=snippets,
            )

        try:
            assessment = CausalAssessment.model_validate(
                {
                    "correlation": correlation,
                    "process_context": process_context,
                    **data,
                    "raw_context_snippets": snippets,
                }
            )
        except ValidationError as exc:
            logger.error("reasoner JSON failed schema: %s\nDATA:\n%s", exc, data)
            return CausalAssessment(
                correlation=correlation,
                process_context=process_context,
                verdict="uncertain",
                verdict_reasoning=f"Reasoner output failed validation: {exc}",
                raw_context_snippets=snippets,
            )
        # Output-side trust enforcement: cap mechanism confidence based on
        # the actual evidence pool, regardless of what the LLM claimed. The
        # system prompt asks the LLM to do this, but the post-validator is
        # the safety net for false-alarm prevention.
        return _apply_tier_caps(assessment, snippets)
