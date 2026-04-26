"""CLI: ingest a document, plain text, or directory into the knowledge graph.

Examples:
  uv run python scripts/ingest.py --file data/sources/cmp_review.pdf
  uv run python scripts/ingest.py --text "CMP downforce affects Cu dishing..."
  uv run python scripts/ingest.py --dir data/sources/
  uv run python scripts/ingest.py --file foo.pdf --no-cognify   # extract only
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

# Allow `python scripts/ingest.py` without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca_knowledge.config import load_settings  # noqa: E402
from rca_knowledge.ingestion.pipeline import IngestionPipeline  # noqa: E402

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    file: Path | None = typer.Option(None, "--file", "-f", help="Path to a PDF/TXT/MD file"),
    directory: Path | None = typer.Option(None, "--dir", "-d", help="Directory of source files"),
    text: str | None = typer.Option(None, "--text", "-t", help="Inline text to ingest"),
    label: str = typer.Option("inline-text", "--label", "-l", help="Source label for inline text"),
    dataset: str = typer.Option("rca", "--dataset", help="Cognee dataset name"),
    cognify: bool = typer.Option(True, "--cognify/--no-cognify", help="Run cognee.cognify after ingestion"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    pipeline = IngestionPipeline(settings)

    if not any([file, directory, text]):
        console.print("[red]Provide one of --file, --dir, or --text[/red]")
        raise typer.Exit(code=2)

    async def run() -> None:
        if file:
            results = await pipeline.ingest_file(file, dataset=dataset, run_cognify=cognify)
        elif directory:
            results = await pipeline.ingest_directory(directory, dataset=dataset, run_cognify=cognify)
        else:
            assert text is not None
            results = await pipeline.ingest_text(text, source_label=label, dataset=dataset, run_cognify=cognify)

        table = Table(title="Ingestion summary", show_lines=False)
        table.add_column("Source")
        table.add_column("Entities", justify="right")
        table.add_column("Relations", justify="right")
        table.add_column("Summary")
        for r in results:
            table.add_row(
                r.source_label,
                str(len(r.extraction.entities)),
                str(len(r.extraction.relations)),
                (r.extraction.summary[:120] + "...") if len(r.extraction.summary) > 120 else r.extraction.summary,
            )
        console.print(table)
        console.print(f"[green]Ingested {len(results)} chunk(s) into dataset '{dataset}'.[/green]")

    asyncio.run(run())


if __name__ == "__main__":
    app()
