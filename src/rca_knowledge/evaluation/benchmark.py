"""Benchmark runner for the causal reasoning query.

The YAML test-case format intentionally mixes:
  - structured fields (correlation, process_context)
  - expected_reasoning_contains: a list of substrings/keywords that should appear
    in the assessment for it to count as on-topic
  - domain_expert_score (optional float 0..1) the user can hand-set as a sanity
    bar — we report both keyword recall and (if provided) the expert score.

The runner does NOT re-train or fine-tune anything; it just exercises the live
graph and reports per-case results plus a roll-up summary.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from rca_knowledge.config import Settings
from rca_knowledge.reasoning.causal_query import CausalAssessment, CausalReasoner

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkCase:
    id: str
    correlation: str
    process_context: str | None = None
    expected_reasoning_contains: list[str] = field(default_factory=list)
    expected_verdict: str | None = None
    domain_expert_score: float | None = None
    notes: str = ""


@dataclass
class BenchmarkResult:
    case_id: str
    verdict: str
    verdict_match: bool | None
    keyword_recall: float
    matched_keywords: list[str]
    missing_keywords: list[str]
    assessment: dict[str, Any]


@dataclass
class BenchmarkReport:
    cases: list[BenchmarkResult]
    summary: dict[str, Any]


def load_cases(yaml_path: Path) -> list[BenchmarkCase]:
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    return [BenchmarkCase(**c) for c in raw.get("cases", [])]


def _score_keywords(assessment: CausalAssessment, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    if not keywords:
        return 1.0, [], []
    blob_parts: list[str] = [
        assessment.verdict_reasoning,
        *(m.description for m in assessment.mechanisms),
        *(c.description for c in assessment.confounders),
        *(c.common_cause for c in assessment.confounders),
        *assessment.suggested_investigations,
        *assessment.knowledge_gaps,
    ]
    blob = " \n ".join(blob_parts).lower()
    matched = [k for k in keywords if k.lower() in blob]
    missing = [k for k in keywords if k.lower() not in blob]
    return len(matched) / len(keywords), matched, missing


async def run_benchmark(settings: Settings, yaml_path: Path) -> BenchmarkReport:
    reasoner = CausalReasoner(settings)
    cases = load_cases(yaml_path)
    results: list[BenchmarkResult] = []

    for case in cases:
        logger.info("running case %s", case.id)
        assessment = await reasoner.assess(
            case.correlation,
            process_context=case.process_context,
        )
        recall, matched, missing = _score_keywords(assessment, case.expected_reasoning_contains)
        verdict_match: bool | None
        if case.expected_verdict is None:
            verdict_match = None
        else:
            verdict_match = assessment.verdict == case.expected_verdict

        results.append(
            BenchmarkResult(
                case_id=case.id,
                verdict=assessment.verdict,
                verdict_match=verdict_match,
                keyword_recall=recall,
                matched_keywords=matched,
                missing_keywords=missing,
                assessment=assessment.model_dump(exclude={"raw_context_snippets"}),
            )
        )

    n = len(results)
    if n == 0:
        summary = {"n_cases": 0}
    else:
        avg_recall = sum(r.keyword_recall for r in results) / n
        verdict_evaluated = [r for r in results if r.verdict_match is not None]
        verdict_acc = (
            sum(1 for r in verdict_evaluated if r.verdict_match) / len(verdict_evaluated)
            if verdict_evaluated
            else None
        )
        summary = {
            "n_cases": n,
            "avg_keyword_recall": round(avg_recall, 3),
            "verdict_accuracy": round(verdict_acc, 3) if verdict_acc is not None else None,
            "verdict_evaluated_n": len(verdict_evaluated),
        }
    return BenchmarkReport(cases=results, summary=summary)


def report_to_json(report: BenchmarkReport) -> str:
    return json.dumps(
        {
            "summary": report.summary,
            "cases": [asdict(r) for r in report.cases],
        },
        indent=2,
        ensure_ascii=False,
    )
