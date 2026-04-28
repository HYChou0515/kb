"""Request / response schemas for the KB API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from rca_knowledge.ingestion.extractor import ExtractionResult
from rca_knowledge.reasoning.causal_query import CausalAssessment

RecallMode = Literal["snippets", "assessment", "synthesis"]
SourceFilter = Literal["literature", "conversations", "rca_reports", "all"]


# ---- retain ----------------------------------------------------------------

class RetainTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    label: str = Field("inline-text", description="Source provenance label")
    dataset: str = "rca"
    cognify: bool = True
    source_kind: Literal["literature", "conversation", "rca_report"] = "literature"


class RetainConversationRequest(BaseModel):
    messages: list[dict] = Field(..., description="[{role, content}] turns")
    session_id: str | None = None
    dataset: str = "rca"
    cognify: bool = True


class RetainExtractionRequest(BaseModel):
    """Push pre-extracted structured knowledge directly into the graph,
    bypassing internal Claude extraction. Caller has presumably run their own
    LLM extraction (Claude/GPT/etc.) and conformed to ExtractionResult.
    """

    extraction: ExtractionResult
    source_label: str
    dataset: str = "rca"
    cognify: bool = True
    source_kind: Literal["literature", "conversation", "rca_report"] = "literature"


class RetainResponse(BaseModel):
    chunks_ingested: int
    entities_extracted: int
    relations_extracted: int
    summary: str = ""
    source_labels: list[str] = []


# ---- recall ----------------------------------------------------------------

class RecallRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: RecallMode = "assessment"
    process_context: str | None = None
    source_filter: SourceFilter = "all"
    top_k: int = 12


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


# ---- admin ----------------------------------------------------------------

class CognifyRequest(BaseModel):
    dataset: str = "rca"


class StatusResponse(BaseModel):
    ok: bool = True
    detail: str = ""
