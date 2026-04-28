# RCA Reports

Agreed-and-finalized RCA reports authored during OpenCode RCA sessions.

## What's in here

Each `RCA-<case_id>-<YYYYMMDD>.md` is a **co-authored markdown** produced by:

1. The OpenCode agent (driving the [rca-agent](../opencode-skill/rca-agent.md) skill)
   walked the user through steps 1–9 of the RCA flow.
2. Step 9.2 ran an iterative agreement loop: agent drafted, expert revised, agent
   re-drafted, until the expert explicitly agreed.
3. Step 9.3 saved the agreed markdown here AND ingested it into the KB at
   `source_kind="rca_report"` (highest trust tier).

## Why these are committed to git

- **Audit trail** — every accepted RCA decision is reproducible from git history
- **Pre-train signal for KB** — when you bootstrap a new KB instance (or wipe
  `.cognee_data/`), re-running `scripts/seed_primer.py`-style ingestion against
  this directory replays all your fab's accumulated RCA knowledge into the new KB.

## Format

Strictly follow the template in [opencode-skill/rca-agent.md](../opencode-skill/rca-agent.md)
section 9.1. Section headers in 繁體中文; technical terms / acronyms / tool IDs
in English (CMP, TDDB, EM, SiO2, ETCH_C, M2_VIA_ETCH, …).

The 7 mandatory sections:
1. 缺陷概述 (Defect Summary)
2. 確認真因 (Confirmed Root Cause)
3. 排除假設 (Ruled-out Hypotheses)
4. 識別之 Confounder
5. 後續 Action Items
6. KB 知識空缺 (Knowledge Gaps)
7. KB 反饋 (KB Feedback) — ★ 學習區
8. (optional) 詞彙表 / Glossary

## Re-ingesting the corpus

If you ever wipe the KB and want to rebuild from this directory:

```bash
for f in reports/RCA-*.md; do
  curl -s -X POST http://127.0.0.1:8765/retain/text \
    -H 'Content-Type: application/json' \
    --data "$(jq -Rs --arg label "$(basename "$f" .md)" \
        '{text: ., label: $label, source_kind: "rca_report", cognify: false}' < "$f")"
done

curl -s -X POST http://127.0.0.1:8765/admin/cognify \
  -H 'Content-Type: application/json' -d '{"dataset":"rca"}'
```
