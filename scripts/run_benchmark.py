"""CLI: run the benchmark suite against the current knowledge graph.

Examples:
  uv run python scripts/run_benchmark.py
  uv run python scripts/run_benchmark.py --cases data/benchmark/test_cases.yaml --out reports/run1.json
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca.container import Container  # noqa: E402
from rca.evaluation.benchmark import (  # noqa: E402
    report_to_json,
    run_benchmark,
)

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    cases: Path = typer.Option(
        Path("data/benchmark/test_cases.yaml"),
        "--cases",
        "-c",
        help="Path to YAML test cases",
    ),
    out: Path | None = typer.Option(None, "--out", "-o", help="Optional JSON output path"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    reasoning = Container().reasoning()

    async def run() -> None:
        report = await run_benchmark(reasoning, cases)

        t = Table(title="Benchmark results")
        t.add_column("Case")
        t.add_column("Verdict")
        t.add_column("Match", justify="center")
        t.add_column("Recall", justify="right")
        t.add_column("Missing keywords")
        for r in report.cases:
            match_str = "—" if r.verdict_match is None else ("✓" if r.verdict_match else "✗")
            t.add_row(
                r.case_id,
                r.verdict,
                match_str,
                f"{r.keyword_recall:.2f}",
                ", ".join(r.missing_keywords) or "—",
            )
        console.print(t)
        console.print(f"[bold]Summary:[/bold] {report.summary}")

        if out is not None:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report_to_json(report), encoding="utf-8")
            console.print(f"[green]Wrote JSON report to {out}[/green]")

    asyncio.run(run())


if __name__ == "__main__":
    app()
