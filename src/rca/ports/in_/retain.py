"""Retain DTOs — request/response shapes for /retain/* endpoints + ExtractionResult."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ─── ExtractionResult and friends ───────────────────────────────────────────
# Co-located here because /retain/extraction takes ExtractionResult as input
# and the SemiconductorExtractionService output is the same type.

EntityType = Literal[
    "process_step",
    "material",
    "defect_type",
    "mechanism",
    "process_parameter",
    "measurement_metric",
    "equipment",
    "layer_or_module",
    "other",
]

RelationType = Literal[
    "causes",
    "inhibits",
    "correlates_with",
    "is_a",
    "part_of",
    "measured_by",
    "occurs_in",
    "produced_by",
    "confounded_by",
]

ConfidenceLevel = Literal[
    "established_physics",
    "empirically_observed",
    "theoretical_or_proposed",
]


class Entity(BaseModel):
    name: str = Field(..., description="Canonical name, prefer common semiconductor terminology")
    type: EntityType
    aliases: list[str] = Field(default_factory=list)
    description: str = Field("", description="One-sentence description")


class Relation(BaseModel):
    source: str
    target: str
    type: RelationType
    mechanism: str = Field(
        "",
        description="1-2 sentence physical/chemical mechanism explaining the relation",
    )
    confidence: ConfidenceLevel = "empirically_observed"
    polarity: Literal["positive", "negative", "unspecified"] = "unspecified"
    notes: str = ""


class ExtractionResult(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    summary: str = Field("", description="2-3 sentence summary of the document's RCA-relevant content")


# ─── /retain/* request / response ───────────────────────────────────────────


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
