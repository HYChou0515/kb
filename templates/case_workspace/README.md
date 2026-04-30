# RCA case workspace

This directory is the working environment for **one** defect-RCA case. It is
hydrated when you `POST /case-study/{id}/open-workspace` and tar-archived
back into `CaseStudy.workspace_archive` when the session closes.

## Files in this workspace

| File | Owner | Purpose |
|---|---|---|
| `CASE.md` | system (auto-rendered) | case metadata — DO NOT edit; edit the CaseStudy record via API instead |
| `AGENTS.md` | system (template) | top-level agent instructions opencode reads at session start |
| `.opencode/agents/rca-agent.md` | system (template) | the 9-step RCA flow skill |
| `notes.md` | agent + you | scratchpad for cumulative observations |
| `draft_report.md` | agent + you | co-authored draft of the RCA report |
| `uploaded_final_report.md` | you (upload) | report draft you uploaded for co-finalization (only present if uploaded) |

## What survives across sessions

Everything in this dir gets tar'd into `CaseStudy.workspace_archive` at
session close, and untar'd back on next open. **`opencode.json` is
intentionally absent** — opencode config is server-managed and injected via
env vars at spawn time so the agent can't modify its own constraints.

## What does NOT survive

- Files in `.opencode/cache/`, `.opencode/tmp/` (per `.gitignore`)
- The opencode session's chat history is in opencode's own SQLite (separate
  from this workspace dir); resume relies on `Session.opencode_session_id`
