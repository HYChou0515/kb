# Primers

Built-in seed corpus for the POC's KB. Each `*.md` file in this directory is
ingested by `scripts/seed_primer.py` (called by `demo.sh`).

## Format

- One primer per file
- Filename stem becomes the source label (e.g. `via-etch-particle-mechanism.md`
  → label `via-etch-particle-mechanism`)
- File body is plain text — no frontmatter, no special syntax. Markdown is
  fine but the LLM extractor reads it as text
- `README.md` and any file starting with `_` are skipped

## Adding a primer

Drop a new `.md` file in this directory. Re-run `./scripts/demo.sh` (or just
`uv run python scripts/seed_primer.py` after the API is running) to ingest it.

## Removing / editing a primer

Delete or edit the file. **Note:** seed_primer.py does NOT remove old facts
from the KB when you change a primer — it only adds. To get a clean re-seed:

```bash
rm -rf .cognee_data .cognee_system
./scripts/demo.sh
```

## What's currently in here

The 8 default primers cover the mechanisms exercised by the mock fab data
demo, especially `M2_VIA_ETCH × ETCH_C → metal_short_M2` (the true root cause
in the mock dataset). They also include some "anti-mechanism" knowledge
(scribe lines and dummy steps don't generate defects) so the agent can
correctly drop spurious correlations in step 8 of the RCA flow.
