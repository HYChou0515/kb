"""End-to-end triage demo — stats algo → KB filter → drop/keep verdict per candidate.

This is the POC punchline in one command, without OpenCode. It:
  1. Calls stats-algo-mcp.compute_factor_scores in-process to get candidates from
     the mock fab data (deliberately noisy — produces false alarms).
  2. For each top-K candidate, calls the KB API's /recall (mode=assessment) in
     parallel to ask whether the (factor → defect) pair has a plausible mechanism.
  3. Prints a triage table: how many false alarms the KB drops vs. keeps.

Examples:
  uv run python scripts/triage.py
  uv run python scripts/triage.py --top-k 15 --defect metal_short_M2
  uv run python scripts/triage.py --json   # machine-readable
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_servers.stats_algo_mcp import compute_factor_scores  # noqa: E402
from rca_knowledge.config import load_settings  # noqa: E402

app = typer.Typer(add_completion=False)
console = Console()

_VERDICT_STYLE = {
    "plausible": "bold green",
    "uncertain": "bold yellow",
    "implausible": "bold red",
}


_RETRY_AFTER_RE = re.compile(r"try again in ([0-9.]+)s", re.IGNORECASE)


def _parse_retry_after(detail: str) -> float | None:
    """Pull the 'try again in 12.84s' from OpenAI 429 messages."""
    m = _RETRY_AFTER_RE.search(detail)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


async def _ask_kb(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    candidate: dict,
    defect_type: str,
    process_context: str,
    *,
    max_retries: int = 3,
) -> dict:
    query = (
        f"Tool {candidate['tool_id']} at step {candidate['process_step']} "
        f"correlates with {defect_type} defects (stat_score={candidate['score']:.2f}, "
        f"n_wafers_with_factor={candidate['n_wafers_with_factor']})"
    )
    payload = {
        "query": query,
        "mode": "assessment",
        "process_context": process_context,
        "top_k": 10,
    }

    async with sem:
        attempt = 0
        while True:
            r = await client.post("/recall", json=payload)
            if r.is_success:
                a = r.json()["assessment"]
                return {
                    "candidate": candidate,
                    "verdict": a.get("verdict", "?"),
                    "verdict_reasoning": a.get("verdict_reasoning", ""),
                    "mechanisms": a.get("mechanisms", []),
                    "confounders": a.get("confounders", []),
                }
            try:
                detail = r.json().get("detail", r.text)
            except Exception:  # noqa: BLE001
                detail = r.text

            # 429 → respect server's retry hint and try again, but only a few times
            is_rate_limit = r.status_code == 429 or "RateLimitError" in detail or "rate_limit" in detail.lower()
            if is_rate_limit and attempt < max_retries:
                wait_s = _parse_retry_after(detail) or (2 ** attempt)
                wait_s = max(wait_s, 1.0) + 0.5  # small safety margin
                console.print(
                    f"[yellow]rate-limited on {candidate['process_step']}::{candidate['tool_id']}, "
                    f"sleeping {wait_s:.1f}s (attempt {attempt+1}/{max_retries})[/yellow]"
                )
                await asyncio.sleep(wait_s)
                attempt += 1
                continue

            return {
                "candidate": candidate,
                "verdict": "ERROR",
                "verdict_reasoning": f"HTTP {r.status_code}: {detail}",
                "mechanisms": [],
                "confounders": [],
            }


@app.command()
def main(
    defect_type: str = typer.Option("metal_short_M2", "--defect", "-d"),
    top_k: int = typer.Option(10, "--top-k", "-k"),
    threshold: float = typer.Option(0.25, "--threshold"),
    process_context: str = typer.Option(
        "BEOL Cu damascene, M2 layer, scan post-M2 CMP",
        "--context",
        "-c",
    ),
    drop_dummy: bool = typer.Option(True, "--drop-dummy/--keep-dummy"),
    concurrency: int = typer.Option(
        3,
        "--concurrency",
        "-j",
        help="Max parallel /recall calls. Lower if you hit OpenAI rate limits "
        "(gpt-4o default is 30K TPM ≈ 3 concurrent requests).",
    ),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    settings = load_settings()
    base = settings.kb_api_base_url

    async def run() -> None:
        console.print(f"[dim]Step 1/3: stats algo on mock fab data (defect={defect_type})...[/dim]")
        scores = await compute_factor_scores(
            defect_type=defect_type,
            drop_dummy_steps=drop_dummy,
            threshold=threshold,
            top_n=top_k,
        )
        cands = scores["candidates"]
        console.print(
            f"[dim]    → {scores['n_factors']} factors over {scores['n_wafers']} wafers; "
            f"{len(cands)} above |r|≥{threshold} (showing top {top_k})[/dim]\n"
        )

        if not cands:
            console.print("[yellow]No candidates above threshold. Mock data not generated?[/yellow]")
            console.print("Run: uv run python data/mock-fab-data/generate.py")
            raise typer.Exit(code=1)

        console.print(
            f"[dim]Step 2/3: asking KB for each candidate "
            f"({len(cands)} requests, concurrency={concurrency})...[/dim]"
        )
        sem = asyncio.Semaphore(concurrency)
        async with httpx.AsyncClient(base_url=base, timeout=httpx.Timeout(120.0)) as c:
            try:
                health = await c.get("/health")
                health.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]ERROR:[/red] KB API not reachable at {base}: {exc}")
                console.print("Start it with [bold]./scripts/demo.sh[/bold] or [bold]uv run kb-api[/bold].")
                raise typer.Exit(code=2)

            results = await asyncio.gather(
                *[_ask_kb(sem, c, ca, defect_type, process_context) for ca in cands]
            )

        if as_json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
            return

        console.print("[dim]Step 3/3: triage decisions[/dim]\n")
        t = Table(title=f"KB-filtered candidates for {defect_type}", show_lines=True)
        t.add_column("Step")
        t.add_column("Tool")
        t.add_column("Stat r", justify="right")
        t.add_column("KB verdict", justify="center")
        t.add_column("Mechanism (1-line)")
        for r in results:
            ca = r["candidate"]
            verdict = r["verdict"]
            style = _VERDICT_STYLE.get(verdict, "white")
            mech_line = ""
            if r["mechanisms"]:
                mech_line = r["mechanisms"][0].get("description", "")[:90]
            elif r["confounders"]:
                mech_line = "(confounder) " + r["confounders"][0].get("description", "")[:78]
            t.add_row(
                ca["process_step"],
                ca["tool_id"],
                f"{ca['score']:+.2f}",
                f"[{style}]{verdict}[/{style}]",
                mech_line,
            )
        console.print(t)

        # rollup
        counts: dict[str, int] = {}
        for r in results:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        n = len(results)
        plausible = counts.get("plausible", 0)
        uncertain = counts.get("uncertain", 0)
        implausible = counts.get("implausible", 0)
        console.print(
            f"\n[bold]Summary:[/bold] "
            f"[green]{plausible} plausible[/green] / "
            f"[yellow]{uncertain} uncertain[/yellow] / "
            f"[red]{implausible} implausible[/red]   "
            f"out of {n} candidates from stats algo"
        )
        if implausible > 0:
            console.print(
                f"\n[bold]→ KB filter dropped {implausible}/{n} "
                f"({implausible*100//n}%) of stats-algo candidates as having no plausible mechanism.[/bold]"
            )

    asyncio.run(run())


if __name__ == "__main__":
    app()
