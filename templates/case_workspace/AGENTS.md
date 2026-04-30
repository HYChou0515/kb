# RCA Agent — workspace instructions

You are running inside a **case workspace** for one specific defect case under
investigation. Read these files at session start:

- **CASE.md** — case metadata (title, description, defect_type, owner, etc.)
  This is your case context. Always read it first.
- **README.md** — human-facing notes about this workspace's structure.
- **notes.md** — your scratchpad for accumulated observations across the
  conversation. Keep it updated as you learn from the user.
- **draft_report.md** — the draft RCA report. You and the user co-author this;
  it becomes the final RCAReport when the user clicks "Submit final" in the UI.

If the user uploaded a final report draft, it's at **uploaded_final_report.md**.
Compare it against your accumulated `notes.md` and the conversation; flag
discrepancies and propose reconciled wording in `draft_report.md`.

---

For the actual 9-step RCA flow, see `.opencode/agents/rca-agent.md`. That file
is the canonical agent skill; this file orients you to the workspace files.
