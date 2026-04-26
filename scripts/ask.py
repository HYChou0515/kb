"""Interactive Q&A against the running KB API.

Examples:
    # one-shot question (assessment mode → structured verdict)
    uv run python scripts/ask.py "Tool ETCH_C at step M2_VIA_ETCH correlates with metal_short_M2"

    # with process context
    uv run python scripts/ask.py -c "BEOL Cu damascene M2 28nm" \\
        "Tool ETCH_C at step M2_VIA_ETCH correlates with metal_short_M2"

    # cheap retrieval — just pull KB snippets, no LLM synthesis
    uv run python scripts/ask.py --mode snippets "via etch particle"

    # prose synthesis (cognee GRAPH_COMPLETION)
    uv run python scripts/ask.py --mode synthesis "What causes M2 metal shorts?"

    # filter retrieval to literature-only or conversation-only
    uv run python scripts/ask.py --source literature "..."

    # JSON output for piping
    uv run python scripts/ask.py --json "..." | jq .
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca_knowledge.config import load_settings  # noqa: E402

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


_VERDICT_STYLE = {
    "plausible": "bold green",
    "uncertain": "bold yellow",
    "implausible": "bold red",
}


def _print_assessment(a: dict) -> None:
    style = _VERDICT_STYLE.get(a.get("verdict", ""), "bold")
    console.print(
        Panel(
            f"[{style}]{a['verdict'].upper()}[/{style}]\n\n{a.get('verdict_reasoning', '')}",
            title=f"Causal assessment — {a.get('correlation', '')}",
            subtitle=a.get("process_context") or "",
        )
    )

    if a.get("mechanisms"):
        t = Table(title="Mechanisms", show_lines=True)
        t.add_column("Confidence")
        t.add_column("Description")
        t.add_column("Citations")
        for m in a["mechanisms"]:
            t.add_row(
                m.get("confidence", "?"),
                m.get("description", ""),
                ", ".join(m.get("citations", [])) or "—",
            )
        console.print(t)

    if a.get("confounders"):
        t = Table(title="Potential confounders", show_lines=True)
        t.add_column("Common cause")
        t.add_column("Description")
        t.add_column("Citations")
        for c in a["confounders"]:
            t.add_row(
                c.get("common_cause", ""),
                c.get("description", ""),
                ", ".join(c.get("citations", [])) or "—",
            )
        console.print(t)

    if a.get("suggested_investigations"):
        console.print("[bold]Suggested investigations:[/bold]")
        for s in a["suggested_investigations"]:
            console.print(f"  • {s}")

    if a.get("knowledge_gaps"):
        console.print("[bold yellow]Knowledge gaps:[/bold yellow]")
        for g in a["knowledge_gaps"]:
            console.print(f"  • {g}")


def _print_snippets(snippets: list[str]) -> None:
    for i, s in enumerate(snippets, 1):
        console.print(Panel(s.strip(), title=f"snippet {i}"))


@app.command()
def main(
    query: str = typer.Argument(..., help="Question / correlation statement"),
    process_context: str | None = typer.Option(None, "--context", "-c"),
    mode: str = typer.Option("assessment", "--mode", "-m", help="assessment | snippets | synthesis"),
    source: str = typer.Option("all", "--source", help="all | literature | conversations"),
    top_k: int = typer.Option(12, "--top-k"),
    as_json: bool = typer.Option(False, "--json", help="Emit raw JSON"),
) -> None:
    settings = load_settings()
    base = settings.kb_api_base_url

    async def run() -> None:
        async with httpx.AsyncClient(base_url=base, timeout=httpx.Timeout(120.0)) as c:
            try:
                health = await c.get("/health")
                health.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]ERROR:[/red] KB API not reachable at {base}: {exc}")
                console.print("Start it with [bold]./scripts/demo.sh[/bold] or [bold]uv run kb-api[/bold].")
                raise typer.Exit(code=2)

            r = await c.post(
                "/recall",
                json={
                    "query": query,
                    "mode": mode,
                    "process_context": process_context,
                    "source_filter": source,
                    "top_k": top_k,
                },
            )
            if not r.is_success:
                try:
                    detail = r.json().get("detail", r.text)
                except Exception:  # noqa: BLE001
                    detail = r.text
                console.print(f"[red]ERROR:[/red] HTTP {r.status_code}: {detail}")
                raise typer.Exit(code=1)

            payload = r.json()

        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return

        if mode == "assessment":
            _print_assessment(payload["assessment"])
        elif mode == "snippets":
            _print_snippets(payload["snippets"])
        elif mode == "synthesis":
            console.print(Panel(payload["synthesis"], title="Synthesis"))
        else:
            console.print(json.dumps(payload, indent=2, ensure_ascii=False))

    asyncio.run(run())


if __name__ == "__main__":
    app()
