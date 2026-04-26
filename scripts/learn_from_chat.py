"""CLI: ingest an RCA conversation log into the knowledge graph.

Conversation file format (JSON or YAML), top-level "messages" list:

    {
      "session_id": "rca-2026-04-26-via-leak",
      "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
      ]
    }

Examples:
  uv run python scripts/learn_from_chat.py --file data/sources/rca_session_001.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca_knowledge.config import load_settings  # noqa: E402
from rca_knowledge.ingestion.pipeline import IngestionPipeline  # noqa: E402

app = typer.Typer(add_completion=False)
console = Console()


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


@app.command()
def main(
    file: Path = typer.Option(..., "--file", "-f"),
    dataset: str = typer.Option("rca", "--dataset"),
    cognify: bool = typer.Option(True, "--cognify/--no-cognify"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    pipeline = IngestionPipeline(settings)
    payload = _load(file)
    messages = payload.get("messages", [])
    if not messages:
        console.print("[red]No messages found in file[/red]")
        raise typer.Exit(code=2)

    async def run() -> None:
        results = await pipeline.ingest_conversation(
            messages,
            session_id=payload.get("session_id"),
            dataset=dataset,
            run_cognify=cognify,
        )
        console.print(f"[green]Ingested {len(results)} chunk(s) from conversation '{payload.get('session_id', file.name)}'.[/green]")
        for r in results:
            console.print(f"  • {r.source_label}: entities={len(r.extraction.entities)} relations={len(r.extraction.relations)}")

    asyncio.run(run())


if __name__ == "__main__":
    app()
