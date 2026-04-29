"""Recall DTOs — request/response shapes for /recall + CausalAssessment."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RecallMode = Literal["snippets", "assessment", "synthesis"]
SourceFilter = Literal["literature", "conversations", "rca_reports", "all"]
Verdict = Literal["plausible", "uncertain", "implausible"]


class MechanismHypothesis(BaseModel):
    description: str = Field(
        ..., description="The proposed causal pathway A→B in 1-2 sentences"
    )
    supporting_entities: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    citations: list[str] = Field(
        default_factory=list, description="Source labels from the graph"
    )


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


class RecallRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: RecallMode = "assessment"
    process_context: str | None = None
    source_filter: SourceFilter = "all"
    top_k: int = 12
    exclude_refuted: bool = False


class RecallSnippetsResponse(BaseModel):
    mode: Literal["snippets"] = "snippets"
    snippets: list[str]


class RecallAssessmentResponse(BaseModel):
    mode: Literal["assessment"] = "assessment"
    assessment: CausalAssessment


class RecallSynthesisResponse(BaseModel):
    mode: Literal["synthesis"] = "synthesis"
    synthesis: str
    raw: list[str] = []
