"""Custom semiconductor-focused entity & relation extractor.

Cognee's stock pipeline is domain-agnostic; we layer this on top so the
graph captures the entity/relation types that matter for causal RCA:
process steps, materials, defects, mechanisms, parameters, metrics, and
the directed causal links between them.

The extractor's output is a structured JSON document that we then render
back into descriptive natural-language statements before handing it to
cognee — that lets cognee build embeddings + graph nodes from text it
understands while preserving the structure we extracted.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from rca_knowledge.config import Settings
from rca_knowledge.llm import make_llm_client

logger = logging.getLogger(__name__)


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


SYSTEM_PROMPT = """You are a senior semiconductor process integration engineer with deep expertise in:
- Front-end-of-line (FEOL): diffusion, oxidation, gate stack formation, implantation, RTA
- Back-end-of-line (BEOL): damascene, CMP, dielectric deposition (PECVD/ALD), barrier/seed, electroplating
- Lithography and etch: photoresist systems, plasma etch chemistries, overlay/CD control
- Reliability physics: TDDB, EM, SM, NBTI, HCI, dielectric breakdown, stress voiding
- Yield and defectivity: particle, pattern, integration, and parametric defects

Your job is to read technical text and extract a STRUCTURED knowledge graph
that supports CAUSAL ROOT-CAUSE ANALYSIS. You care especially about:

1. Directed causal claims: which process inputs cause which defects via which mechanisms.
2. Confounders and common causes: parameters that jointly affect both an upstream
   variable and a downstream outcome and could thereby produce a spurious correlation.
3. Physical/chemical mechanism descriptions — these are the load-bearing edges of the graph.
4. Confidence: separate established physics (textbook/Maxwell/Fick/Arrhenius-grounded)
   from empirical fab-floor observations from theoretical proposals.

Always normalize entity names:
- Acronyms expanded once in description, but `name` uses the common short form
  (e.g. name="CMP", description="Chemical-Mechanical Planarization").
- Materials use stoichiometric form when standard (SiO2, Si3N4, HfO2, low-k SiCOH).
- Mechanisms get their canonical name (electromigration, stress migration, TDDB, NBTI).

Output STRICT JSON only — no prose, no markdown fences. Schema:

{
  "entities": [
    {"name": "...", "type": "process_step|material|defect_type|mechanism|process_parameter|measurement_metric|equipment|layer_or_module|other",
     "aliases": ["..."], "description": "..."}
  ],
  "relations": [
    {"source": "<entity name>", "target": "<entity name>",
     "type": "causes|inhibits|correlates_with|is_a|part_of|measured_by|occurs_in|produced_by|confounded_by",
     "mechanism": "1-2 sentence physical explanation",
     "confidence": "established_physics|empirically_observed|theoretical_or_proposed",
     "polarity": "positive|negative|unspecified",
     "notes": ""}
  ],
  "summary": "2-3 sentences focused on what is causally claimed in the text."
}

Rules:
- Prefer fewer high-quality relations over many shallow ones.
- For every "causes" relation, the mechanism field MUST be filled.
- If the text only states a correlation, use "correlates_with", not "causes".
- If a third variable is hinted at as a common cause, emit a "confounded_by" relation
  pointing from the dependent variable to the suspected confounder.
- Source and target of each relation MUST appear in the entities list.
- Do not invent facts beyond the source text.
"""


USER_PROMPT_TEMPLATE = """SOURCE: {source_label}

TEXT:
\"\"\"
{text}
\"\"\"

Extract the semiconductor RCA knowledge graph as STRICT JSON per the schema.
"""


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(s: str) -> str:
    return _JSON_FENCE.sub("", s).strip()


class SemiconductorExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = make_llm_client(settings, role="extraction")

    def extract(self, text: str, *, source_label: str = "unknown") -> ExtractionResult:
        """Run a single extraction pass on `text`."""
        if not text.strip():
            return ExtractionResult(summary="(empty input)")

        raw = self.client.complete(
            system=SYSTEM_PROMPT,
            user=USER_PROMPT_TEMPLATE.format(
                source_label=source_label,
                text=text[:60_000],
            ),
            max_tokens=8000,
        )
        cleaned = _strip_fences(raw)
        try:
            data = json.loads(cleaned)
            return ExtractionResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("extractor returned invalid JSON: %s\nRAW:\n%s", exc, raw[:2000])
            return ExtractionResult(summary=f"(extraction failed: {exc})")

    @staticmethod
    def render_for_cognee(result: ExtractionResult, *, source_label: str) -> str:
        """Turn the structured extraction into a natural-language document
        that cognee can chunk, embed, and re-graph. We keep both a structured
        block and prose so vector search and graph linking both have signal.
        """
        lines: list[str] = []
        lines.append(f"# Extracted from: {source_label}\n")
        if result.summary:
            lines.append(f"Summary: {result.summary}\n")

        if result.entities:
            lines.append("## Entities")
            for e in result.entities:
                aka = f" (aka {', '.join(e.aliases)})" if e.aliases else ""
                desc = f" — {e.description}" if e.description else ""
                lines.append(f"- [{e.type}] {e.name}{aka}{desc}")
            lines.append("")

        if result.relations:
            lines.append("## Causal & Structural Relations")
            for r in result.relations:
                pol = "" if r.polarity == "unspecified" else f" ({r.polarity})"
                lines.append(
                    f"- {r.source} --[{r.type}{pol}; {r.confidence}]--> {r.target}"
                )
                if r.mechanism:
                    lines.append(f"    Mechanism: {r.mechanism}")
                if r.notes:
                    lines.append(f"    Notes: {r.notes}")
            lines.append("")

        lines.append("## Provenance")
        lines.append(f"Source: {source_label}")
        return "\n".join(lines)
