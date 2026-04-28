"""Batch-ingest a directory of source documents into the KB.

Walks a directory, uploads every supported file to the KB API's
``/retain/file`` endpoint, then runs a single ``/admin/cognify`` at the end.

Examples:
  # default: ingest data/sources/ as literature
  uv run python scripts/seed_corpus.py data/sources

  # ingest a folder of past RCA reports as the highest trust tier
  uv run python scripts/seed_corpus.py reports/ --source-kind rca_report

  # ingest expert chat transcripts
  uv run python scripts/seed_corpus.py data/transcripts/ --source-kind conversation

  # dry run — list what would be uploaded
  uv run python scripts/seed_corpus.py data/sources --dry-run

  # tune concurrency to fit your OpenAI rate limit
  uv run python scripts/seed_corpus.py data/sources -j 1
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca_knowledge.config import load_settings  # noqa: E402

app = typer.Typer(add_completion=False)
console = Console()

DEFAULT_EXTS = {".pdf", ".md", ".txt", ".rst"}
DEFAULT_EXCLUDE_NAMES = {"README.md", "readme.md", ".gitkeep"}


def _collect_files(
    root: Path,
    exts: set[str],
    recursive: bool,
    exclude_names: set[str],
) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(f"{root} does not exist")
    if root.is_file():
        return [root] if root.suffix.lower() in exts else []
    pattern = "**/*" if recursive else "*"
    out: list[Path] = []
    for p in sorted(root.glob(pattern)):
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        if p.name in exclude_names or p.name.startswith("_"):
            continue
        out.append(p)
    return out


async def _upload(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    file_path: Path,
    *,
    label: str,
    source_kind: str,
    dataset: str,
    max_retries: int = 3,
) -> tuple[Path, dict | None, str | None]:
    """Upload one file. Returns (path, summary, error)."""
    async with sem:
        attempt = 0
        while True:
            try:
                with file_path.open("rb") as fh:
                    files = {"file": (file_path.name, fh, "application/octet-stream")}
                    data = {
                        "label": label,
                        "source_kind": source_kind,
                        "dataset": dataset,
                        "cognify": "false",  # batch cognify at end
                    }
                    r = await client.post("/retain/file", files=files, data=data)
            except Exception as exc:  # noqa: BLE001
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    attempt += 1
                    continue
                return file_path, None, f"network: {exc.__class__.__name__}: {exc}"

            if r.is_success:
                return file_path, r.json(), None

            try:
                detail = r.json().get("detail", r.text)
            except Exception:  # noqa: BLE001
                detail = r.text
            is_rate_limit = r.status_code == 429 or "rate_limit" in detail.lower()
            if is_rate_limit and attempt < max_retries:
                wait = 5 * (2 ** attempt)
                console.print(
                    f"[yellow]rate-limited on {file_path.name}, sleeping {wait}s "
                    f"(attempt {attempt+1}/{max_retries})[/yellow]"
                )
                await asyncio.sleep(wait)
                attempt += 1
                continue
            return file_path, None, f"HTTP {r.status_code}: {detail}"


@app.command()
def main(
    directory: Path = typer.Argument(..., help="Directory or single file to ingest"),
    source_kind: str = typer.Option(
        "literature",
        "--source-kind",
        "-s",
        help="literature | conversation | rca_report",
    ),
    label_prefix: str = typer.Option("", "--label-prefix", help="Prefix added to every label"),
    extensions: str = typer.Option(
        ".pdf,.md,.txt,.rst",
        "--ext",
        help="Comma-separated file extensions to include",
    ),
    exclude: str = typer.Option(
        "README.md,readme.md,.gitkeep",
        "--exclude",
        help="Comma-separated filenames to skip (in addition to files starting with _)",
    ),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive"),
    concurrency: int = typer.Option(
        2,
        "--concurrency",
        "-j",
        help="Max parallel uploads (lower = safer for OpenAI TPM)",
    ),
    dataset: str = typer.Option("rca", "--dataset"),
    cognify_at_end: bool = typer.Option(True, "--cognify/--no-cognify"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    settings = load_settings()
    base = settings.kb_api_base_url

    exts = {e if e.startswith(".") else f".{e}" for e in extensions.lower().split(",") if e.strip()}
    exclude_names = {n.strip() for n in exclude.split(",") if n.strip()}

    files = _collect_files(directory.resolve(), exts, recursive, exclude_names)
    if not files:
        console.print(
            f"[yellow]No files matching {sorted(exts)} found in {directory} "
            f"(recursive={recursive}, exclude={sorted(exclude_names)}).[/yellow]"
        )
        raise typer.Exit(code=1)

    console.print(f"Found [bold]{len(files)}[/bold] file(s) to ingest into KB at {base}")
    console.print(f"  source_kind = [cyan]{source_kind}[/cyan]")
    console.print(f"  dataset     = {dataset}")
    console.print(f"  concurrency = {concurrency}")
    if label_prefix:
        console.print(f"  label_prefix= [cyan]{label_prefix}[/cyan]")

    if dry_run:
        for p in files:
            console.print(f"  [dim]would upload[/dim] {p}")
        console.print("[dim](dry run; nothing sent)[/dim]")
        return

    async def run() -> None:
        sem = asyncio.Semaphore(concurrency)
        successes: list[tuple[Path, dict]] = []
        errors: list[tuple[Path, str]] = []

        async with httpx.AsyncClient(base_url=base, timeout=httpx.Timeout(300.0)) as c:
            try:
                health = await c.get("/health")
                health.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]ERROR:[/red] KB API not reachable at {base}: {exc}")
                console.print("Start it with [bold]./scripts/demo.sh[/bold] or [bold]uv run kb-api[/bold].")
                raise typer.Exit(code=2)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            ) as progress:
                task = progress.add_task("ingesting", total=len(files))

                async def _one(p: Path) -> None:
                    label = f"{label_prefix}{p.relative_to(directory.resolve()) if directory.is_dir() else p.name}"
                    fp, summary, err = await _upload(
                        sem, c, p,
                        label=str(label),
                        source_kind=source_kind,
                        dataset=dataset,
                    )
                    if err:
                        errors.append((fp, err))
                    else:
                        assert summary is not None
                        successes.append((fp, summary))
                    progress.update(task, advance=1)

                await asyncio.gather(*[_one(p) for p in files])

            if cognify_at_end and successes:
                console.print("\n[dim]Running /admin/cognify (this may take a while for large corpora)...[/dim]")
                try:
                    r = await c.post("/admin/cognify", json={"dataset": dataset})
                    r.raise_for_status()
                    console.print(f"[green]✓ {r.json().get('detail', 'cognify done')}[/green]")
                except Exception as exc:  # noqa: BLE001
                    console.print(f"[red]cognify failed: {exc}[/red]")

        # Summary
        console.print()
        console.print(f"[bold]Done.[/bold] {len(successes)}/{len(files)} files ingested successfully.")
        total_e = sum(s[1].get("entities_extracted", 0) for s in successes)
        total_r = sum(s[1].get("relations_extracted", 0) for s in successes)
        total_chunks = sum(s[1].get("chunks_ingested", 0) for s in successes)
        console.print(
            f"  Aggregate: {total_chunks} chunks, "
            f"{total_e} entities, {total_r} relations extracted."
        )
        if errors:
            console.print(f"\n[red]{len(errors)} failure(s):[/red]")
            for p, err in errors:
                console.print(f"  [red]✗[/red] {p}: {err}")
            raise typer.Exit(code=1)

    asyncio.run(run())


if __name__ == "__main__":
    app()
