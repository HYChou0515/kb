"""Seed the KB with the built-in semiconductor primer corpus.

Used by scripts/demo-rca-ui.sh to make the KB non-empty before the demo.

Primer documents live in `data/primers/*.md` — one file per primer, filename
stem is the source label, body is plain text.

Calls POST /remember on kb-api with dataset_name="rca_literature" so the
trust-tier signal is preserved at recall time.

Idempotent: re-running adds more entries (cognee dedupes at embedding time).
For a clean re-seed, DELETE /forget?dataset=rca_literature first, or
DELETE /forget?everything=true to wipe the whole graph.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIMER_DIR = PROJECT_ROOT / "data" / "primers"
PRIMER_EXTS = {".md", ".txt"}
PRIMER_SKIP_NAMES = {"README.md", "readme.md"}


def load_primers() -> list[tuple[str, str]]:
    if not PRIMER_DIR.exists():
        raise FileNotFoundError(
            f"{PRIMER_DIR} not found. Create it and drop *.md primer files."
        )
    primers: list[tuple[str, str]] = []
    for p in sorted(PRIMER_DIR.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in PRIMER_EXTS:
            continue
        if p.name in PRIMER_SKIP_NAMES or p.name.startswith("_"):
            continue
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            continue
        primers.append((p.stem, text))
    return primers


async def main() -> None:
    base = os.environ.get("KB_API_BASE_URL", "http://127.0.0.1:8765")
    primers = load_primers()
    if not primers:
        print(f"No primer files in {PRIMER_DIR}. Nothing to seed.")
        return
    print(
        f"Seeding {len(primers)} primer files from {PRIMER_DIR}\n"
        f"  → POST {base}/remember (dataset_name=rca_literature)"
    )

    async with httpx.AsyncClient(base_url=base, timeout=httpx.Timeout(300.0)) as c:
        try:
            r = await c.get("/health")
            r.raise_for_status()
        except Exception as exc:
            print(f"ERROR: KB API not reachable at {base}: {exc}")
            print("Make sure `uv run kb-api` is running.")
            raise

        for label, text in primers:
            # self_improvement=False so we batch-improve at the end (cheaper).
            r = await c.post(
                "/remember",
                json={
                    "text": text,
                    "dataset_name": "rca_literature",
                    "label": label,
                    "self_improvement": False,
                },
            )
            r.raise_for_status()
            print(f"  ✓ remembered: {label} ({len(text)} chars)")

        print("Running improve on rca_literature (this may take a moment)…")
        r = await c.post(
            "/improve", json={"dataset": "rca_literature", "run_in_background": False}
        )
        r.raise_for_status()
        print("  ✓ improve done")


if __name__ == "__main__":
    asyncio.run(main())
