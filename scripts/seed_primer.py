"""Seed the KB with the built-in semiconductor primer corpus.

Used by scripts/demo.sh to make the KB non-empty before the demo.

Primer documents live in `data/primers/*.md` — one file per primer, filename
stem is the source label, body is plain text. Edit / add / remove files in
that directory to change the seed corpus; no code changes needed.

Idempotent: re-running just adds more chunks (cognee will dedupe at
embedding time). For a clean re-seed, prune .cognee_data + .cognee_system
first.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rca_knowledge.config import load_settings  # noqa: E402

PRIMER_DIR = Path(__file__).resolve().parents[1] / "data" / "primers"
PRIMER_EXTS = {".md", ".txt"}
PRIMER_SKIP_NAMES = {"README.md", "readme.md"}


def load_primers() -> list[tuple[str, str]]:
    """Read every primer file in PRIMER_DIR. Returns [(label, text), ...]."""
    if not PRIMER_DIR.exists():
        raise FileNotFoundError(
            f"{PRIMER_DIR} not found. Create it and drop *.md primer files "
            "(see data/primers/README.md for the format)."
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


def _check_response(r: httpx.Response, what: str) -> dict:
    """Like raise_for_status, but prints the server's actual error body
    before raising. The KB API returns JSON {detail, exception_type, path}.
    """
    if r.is_success:
        return r.json()
    body = r.text
    try:
        body_json = r.json()
        detail = body_json.get("detail", body)
    except Exception:
        detail = body
    print(f"ERROR: {what} → HTTP {r.status_code}")
    print(f"  detail: {detail}")
    r.raise_for_status()
    return {}


async def main() -> None:
    settings = load_settings()
    base = settings.kb_api_base_url
    primers = load_primers()
    if not primers:
        print(f"No primer files found in {PRIMER_DIR}. Nothing to seed.")
        return
    print(f"Seeding {len(primers)} primer chunks from {PRIMER_DIR} into {base}/retain/text ...")
    print(f"  LLM provider: {settings.llm_provider}, model: {settings.llm_model}")

    async with httpx.AsyncClient(base_url=base, timeout=httpx.Timeout(300.0)) as c:
        try:
            r = await c.get("/health")
            r.raise_for_status()
        except Exception as exc:
            print(f"ERROR: KB API not reachable at {base}: {exc}")
            print("Make sure `uv run kb-api` is running, OR run this from demo.sh which starts it.")
            raise

        for label, text in primers:
            r = await c.post(
                "/retain/text",
                json={
                    "text": text.strip(),
                    "label": label,
                    "source_kind": "literature",
                    "cognify": False,  # batch cognify at end
                },
            )
            data = _check_response(r, f"retain/text label={label}")
            print(
                f"  ✓ {label}: entities={data['entities_extracted']} "
                f"relations={data['relations_extracted']}"
            )

        print("Running cognify on the dataset (this may take ~30s)...")
        r = await c.post("/admin/cognify", json={"dataset": "rca"})
        data = _check_response(r, "admin/cognify")
        print(f"  ✓ {data['detail']}")


if __name__ == "__main__":
    asyncio.run(main())
