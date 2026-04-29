"""E2E: real cognee + real corpus + real LLM.

Two test groups:

1. **status-filter contract** (the load-bearing invariant of the
   verification design) — write 4 RCAReport chunks under distinct
   `rca_reports_<status>` node_sets, cognify, then recall with a
   node_set filter and assert ONLY the matching status' content
   comes back. If this fails, the whole status-aware mirror is
   decorative; the reasoner cannot trust manager-signoff weighting.

2. **primer corpus recall** — ingest the 9 domain primer markdowns,
   cognify, then for each benchmark case run recall with the
   case's `correlation` query and assert the
   `expected_reasoning_contains` keywords surface in the top-k.
   Catches regressions where ingestion wires correctly but the
   graph-build step silently drops content.

Session-scoped fixture builds the corpus once (cognify is the
expensive step; recall queries are cheap). Tests run against the
live cognee instance — no mocks, no in-memory fakes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from rca.domain.types import VerificationStatus

pytestmark = pytest.mark.integration


# ─── corpus seed data ──────────────────────────────────────────────────────

# Each status gets a chunk with a UNIQUE distinguishing keyword so the
# recall assertions can deterministically check which chunk came back
# (LLM-non-determinism in cognify entity extraction is fine — keywords
# survive into the chunk text verbatim).
_STATUS_CHUNKS: dict[VerificationStatus, dict[str, str]] = {
    "unverified": {
        "marker": "ZIRCONIUM-HYPOTHESIS-MARKER",
        "text": (
            "# RCA Report (unverified)\n"
            "Hypothesis: ZIRCONIUM-HYPOTHESIS-MARKER contamination on chamber walls "
            "may be the root cause of yield drop on tool ETCH-04. Pending physical "
            "verification by FIB cross-section."
        ),
    },
    "partial": {
        "marker": "TUNGSTEN-PARTIAL-MARKER",
        "text": (
            "# RCA Report (partial)\n"
            "TUNGSTEN-PARTIAL-MARKER deposition rate drift confirmed on PVD-02; "
            "partial — root mechanism (target erosion vs gas flow MFC drift) not "
            "yet isolated. One of two candidate causes ruled out."
        ),
    },
    "verified": {
        "marker": "TITANIUM-CONFIRMED-MARKER",
        "text": (
            "# RCA Report (verified)\n"
            "TITANIUM-CONFIRMED-MARKER barrier thinning at via M2 confirmed by "
            "FIB-SEM and TEM EELS profile. Root cause: PVD target end-of-life "
            "shadowing. Manager signoff complete."
        ),
    },
    "refuted": {
        "marker": "COBALT-REFUTED-MARKER",
        "text": (
            "# RCA Report (refuted)\n"
            "Initial COBALT-REFUTED-MARKER silicide hypothesis ruled out — "
            "RBS measurement showed no Co diffusion into channel. Yield drop "
            "traced to a separate lithography overlay issue instead."
        ),
    },
}


# ─── session fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="session")
async def graph_with_corpus(container, project_root: Path):
    """Build the corpus once: 4 status-tagged chunks + 9 primer markdowns,
    cognify, yield the graph adapter for recall queries.

    Teardown calls forget() to clear the tmpdir-rooted cognee state — not
    strictly necessary (tmpdir gets cleaned anyway) but keeps assertions
    in the post-yield phase safe if anyone adds them."""
    graph = container.graph()
    await graph.setup()

    # 4 status-tagged RCA chunks
    for status, payload in _STATUS_CHUNKS.items():
        await graph.remember_text(
            payload["text"],
            dataset="rca",
            node_set=["rca_reports", f"rca_reports_{status}"],
        )

    # 9 primer markdowns
    primers_dir = project_root / "data" / "primers"
    for md in sorted(primers_dir.glob("*.md")):
        if md.name == "README.md":
            continue
        await graph.remember_text(
            md.read_text(encoding="utf-8"),
            dataset="rca",
            node_set=["rca_literature", "rca_primer"],
        )

    # One cognify pass over the whole batch — this is the expensive call.
    await graph.cognify(dataset="rca")

    yield graph

    await graph.forget()


@pytest.fixture(scope="session")
def benchmark_cases(project_root: Path) -> list[dict[str, Any]]:
    raw = (project_root / "data" / "benchmark" / "test_cases.yaml").read_text()
    return yaml.safe_load(raw)["cases"]


# ─── status-filter contract (the killer test) ──────────────────────────────


@pytest.mark.parametrize("target_status", list(_STATUS_CHUNKS.keys()))
async def test_recall_with_node_set_returns_only_matching_status(
    graph_with_corpus, target_status: VerificationStatus
) -> None:
    """The whole point of status-aware mirroring: at recall time, filtering
    by `rca_reports_<status>` returns ONLY chunks tagged with that status,
    not chunks from other statuses.

    If this fails, mirror writes the right tags but recall ignores them —
    verification_status is decorative and the reasoner can't trust it."""
    target_marker = _STATUS_CHUNKS[target_status]["marker"]
    other_markers = [
        payload["marker"]
        for status, payload in _STATUS_CHUNKS.items()
        if status != target_status
    ]

    results = await graph_with_corpus.recall(
        f"What does the report say about {target_marker}?",
        node_set=[f"rca_reports_{target_status}"],
        top_k=20,
    )

    # cognee returns SearchResult-shaped objects; flatten to text
    blob = "\n".join(_result_text(r) for r in results)

    assert target_marker in blob, (
        f"target chunk for status={target_status} ({target_marker}) "
        f"missing from recall — node_set filter excluded too aggressively"
    )
    leaked = [m for m in other_markers if m in blob]
    assert not leaked, (
        f"node_set filter leaked chunks from other statuses: {leaked} "
        f"(expected only rca_reports_{target_status} content)"
    )


# ─── primer corpus recall (regression on cognify pipeline) ─────────────────


@pytest.mark.parametrize(
    "case_id",
    [
        "tc001-cmp-via-resistance",
        "tc002-pecvd-pressure-particle",
        "tc003-anneal-temp-vt-shift",
    ],
)
async def test_recall_primer_corpus_surfaces_expected_keywords(
    graph_with_corpus, benchmark_cases: list[dict[str, Any]], case_id: str
) -> None:
    """For each benchmark case, recall with the correlation query and
    assert at least one expected_reasoning_contains keyword surfaces.

    Keyword presence (case-insensitive substring) is the right tolerance
    band for LLM-non-deterministic cognify+recall — exact-match would be
    flaky, semantic-similarity would need its own scorer."""
    case = next(c for c in benchmark_cases if c["id"] == case_id)
    expected_keywords = [kw.lower() for kw in case["expected_reasoning_contains"]]

    results = await graph_with_corpus.recall(
        case["correlation"],
        top_k=10,
    )
    blob = "\n".join(_result_text(r) for r in results).lower()

    hits = [kw for kw in expected_keywords if kw in blob]
    assert hits, (
        f"benchmark {case_id}: none of {expected_keywords} found in recall "
        f"results — primer ingestion or recall is broken. Result blob "
        f"(first 500 chars): {blob[:500]!r}"
    )


# ─── helpers ───────────────────────────────────────────────────────────────


def _result_text(result: Any) -> str:
    """cognee SearchResult shape varies by SearchType — defensively
    extract text/content/answer fields without assuming structure."""
    for attr in ("text", "content", "answer", "context"):
        v = getattr(result, attr, None)
        if isinstance(v, str) and v:
            return v
    if isinstance(result, dict):
        for k in ("text", "content", "answer", "context"):
            v = result.get(k)
            if isinstance(v, str) and v:
                return v
    return str(result)
