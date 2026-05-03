# RCA Agent — workspace orientation

You are running inside a **case workspace** for one specific defect case under
investigation. The 9-step RCA flow you must follow is **already in your
system prompt** (loaded from `OPENCODE_CONFIG_DIR` at startup). Do not try
to read or search for `.opencode/agents/rca-agent.md` — that file lives
outside the workspace by design and is not reachable from here.

## Files in this workspace

Read these at session start (always start with CASE.md):

- **CASE.md** — case metadata (title, description, defect_type, owner, etc.)
  Authoritative case context, rendered from the CaseStudy record.
- **README.md** — human-facing notes about this workspace's structure.
- **notes.md** — your scratchpad for accumulated observations across the
  conversation. Keep it updated as you learn from the user.
- **draft_report.md** — the draft RCA report. You and the user co-author this;
  it becomes the final RCAReport when the user clicks "Submit final" in the UI.

If the user uploaded a final report draft, it's at **uploaded_final_report.md**.
Compare it against your accumulated `notes.md` and the conversation; flag
discrepancies and propose reconciled wording in `draft_report.md`.

## Where data and tools live

You **cannot** see fab data, MCP server code, or the project repo via the
filesystem — `permission.external_directory = deny` confines every file
tool (read / edit / bash / glob / grep / list) to this workspace dir only.
That's intentional.

Wafer data, defect counts, and RCA scoring are **only** reachable via MCP:

- `wafer-data-mcp.list_lots` / `get_defect_summary` / `download_wafer_history`
- `stats-algo-mcp.compute_factor_scores`
- `kb-mcp.recall_assessment` / `recall_snippets` / `retain_text`

If an MCP returns "data not found", the fix is **not** to `ls data/` from
the workspace (the data lives outside, you can't reach it). Surface the
error to the user; the operator is responsible for bootstrapping the data
via `./scripts/demo.sh` step 3 on the host.
