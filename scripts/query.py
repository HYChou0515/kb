"""CLI: run a causal-plausibility query against the knowledge graph.

Examples:
  uv run python scripts/query.py \
      --correlation "CMP downforce correlates with via resistance at r=0.68" \
      --context "Cu damascene M2, 28nm"

  uv run python scripts/query.py -c "..." -p "..." --json   # JSON output
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca.container import Container  # noqa: E402

app = typer.Typer(add_completion=False)
console = Console()


_VERDICT_STYLE = {
    "plausible": "bold green",
    "uncertain": "bold yellow",
    "implausible": "bold red",
}


def _print_assessment(assessment) -> None:
    style = _VERDICT_STYLE.get(assessment.verdict, "bold")
    console.print(
        Panel(
            f"[{style}]{assessment.verdict.upper()}[/{style}]\n\n{assessment.verdict_reasoning}",
            title=f"Causal assessment — {assessment.correlation}",
            subtitle=assessment.process_context or "",
        )
    )

    if assessment.mechanisms:
        t = Table(title="Mechanisms", show_lines=True)
        t.add_column("Confidence")
        t.add_column("Description")
        t.add_column("Citations")
        for m in assessment.mechanisms:
            t.add_row(m.confidence, m.description, ", ".join(m.citations) or "—")
        console.print(t)

    if assessment.confounders:
        t = Table(title="Potential confounders", show_lines=True)
        t.add_column("Common cause")
        t.add_column("Description")
        t.add_column("Citations")
        for c in assessment.confounders:
            t.add_row(c.common_cause, c.description, ", ".join(c.citations) or "—")
        console.print(t)

    if assessment.suggested_investigations:
        console.print("[bold]Suggested investigations:[/bold]")
        for s in assessment.suggested_investigations:
            console.print(f"  • {s}")

    if assessment.knowledge_gaps:
        console.print("[bold yellow]Knowledge gaps:[/bold yellow]")
        for g in assessment.knowledge_gaps:
            console.print(f"  • {g}")


@app.command()
def main(
    correlation: str = typer.Option(..., "--correlation", "-c"),
    process_context: str | None = typer.Option(None, "--context", "-p"),
    top_k: int = typer.Option(12, "--top-k"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    reasoner = Container().reasoning()

    async def run() -> None:
        assessment = await reasoner.assess(correlation, process_context=process_context, top_k=top_k)
        if as_json:
            print(json.dumps(assessment.model_dump(exclude={"raw_context_snippets"}), indent=2, ensure_ascii=False))
        else:
            _print_assessment(assessment)

    asyncio.run(run())


if __name__ == "__main__":
    app()
