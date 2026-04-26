"""Causal reasoning query.

Given a statistical correlation, produce a structured assessment grounded
in the knowledge graph: known mechanisms, alternative confounders, and
a plausibility verdict with citations.

The retrieval strategy is deliberately broad:
  1. Run a graph-completion search for the correlation statement.
  2. Run an "insights" search for the variables in isolation to surface
     adjacent mechanisms that may not be in the direct neighborhood.
  3. Bundle the retrieved context into a reasoning prompt and let the
     configured LLM (OpenAI or Anthropic) produce the structured assessment.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal

from cognee.api.v1.search import SearchType
from pydantic import BaseModel, Field, ValidationError

from rca_knowledge.config import Settings
from rca_knowledge.graph.cognee_client import CogneeClient
from rca_knowledge.llm import make_llm_client

logger = logging.getLogger(__name__)


Verdict = Literal["plausible", "uncertain", "implausible"]


class MechanismHypothesis(BaseModel):
    description: str = Field(..., description="The proposed causal pathway A→B in 1-2 sentences")
    supporting_entities: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    citations: list[str] = Field(default_factory=list, description="Source labels from the graph")


class ConfounderHypothesis(BaseModel):
    common_cause: str
    description: str
    citations: list[str] = Field(default_factory=list)


class CausalAssessment(BaseModel):
    correlation: str
    process_context: str | None = None
    verdict: Verdict
    verdict_reasoning: str
    mechanisms: list[MechanismHypothesis] = Field(default_factory=list)
    confounders: list[ConfounderHypothesis] = Field(default_factory=list)
    suggested_investigations: list[str] = Field(default_factory=list)
    knowledge_gaps: list[str] = Field(default_factory=list)
    raw_context_snippets: list[str] = Field(default_factory=list, exclude=True)


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


def _stringify_results(results: list[Any]) -> list[str]:
    """Cognee returns heterogeneous payloads depending on SearchType.

    We coerce everything to strings so the reasoner gets readable context.
    """
    out: list[str] = []
    for r in results:
        if isinstance(r, str):
            out.append(r)
        elif isinstance(r, dict):
            out.append(json.dumps(r, ensure_ascii=False, default=str))
        else:
            out.append(str(r))
    return out


class CausalReasoner:
    def __init__(self, settings: Settings, cognee_client: CogneeClient | None = None) -> None:
        self.settings = settings
        self.client = make_llm_client(settings, role="reasoning")
        self.cognee = cognee_client or CogneeClient(settings)

    async def retrieve_context(
        self,
        correlation: str,
        process_context: str | None,
        *,
        top_k: int = 12,
    ) -> list[str]:
        """Pull relevant snippets from the graph using a few search strategies.

        cognee 1.0 reshuffled the SearchType enum (e.g. ``INSIGHTS`` was renamed
        to ``TRIPLET_COMPLETION``). We resolve type names via ``getattr`` so a
        missing variant degrades gracefully instead of crashing the request.
        """
        await self.cognee.setup()
        full_query = correlation if not process_context else f"{correlation}\nContext: {process_context}"

        # Preferred order: rich synthesis, then chunks.
        # NOTE: cognee 1.0 also offers TRIPLET_COMPLETION, but it requires
        # the `create_triplet_embeddings` memify pipeline + User object,
        # which conflicts with our ENABLE_BACKEND_ACCESS_CONTROL=false
        # POC mode. GRAPH_COMPLETION + CHUNKS already gives reliable
        # context for the assessment LLM.
        wanted_names = (
            "GRAPH_COMPLETION",
            "INSIGHTS",  # legacy cognee <1.0
            "CHUNKS",
        )
        search_types = [
            getattr(SearchType, name)
            for name in wanted_names
            if hasattr(SearchType, name)
        ]

        snippets: list[str] = []
        for st in search_types:
            try:
                res = await self.cognee.search(full_query, search_type=st, top_k=top_k)
                snippets.extend(_stringify_results(res))
            except Exception as exc:  # individual SearchType variants may still fail at runtime
                logger.debug("search(%s) failed: %s", st, exc)

        # de-dup while preserving order
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
    ) -> CausalAssessment:
        snippets = await self.retrieve_context(correlation, process_context, top_k=top_k)
        context_block = (
            "\n\n".join(f"[snippet-{i+1}]\n{s}" for i, s in enumerate(snippets))
            if snippets
            else "(no relevant graph context found)"
        )
        user = REASONING_USER_TEMPLATE.format(
            correlation=correlation,
            process_context=process_context or "(none provided)",
            context_block=context_block[:80_000],
        )
        raw = self.client.complete(
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
        return assessment
