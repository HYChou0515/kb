# Demo: end-to-end RCA user flow (phases 5–12)

A copy-paste runbook for verifying the workspace + opencode lifecycle:
**create case → open workspace → chat → soft-close → resume → upload report
→ finalize → stale-notify**.

Audience: developers verifying the phases 5–12 flow works end-to-end.

---

## Prereq

1. **KB API running** — start it with `./scripts/demo.sh` (handles `uv sync`,
   embedding server, KB API on port `8765`, primer seed). Leave it tailing in
   one terminal.
2. **opencode CLI on `PATH`** — this demo spawns a real opencode subprocess
   (default port `4096`) and opens a browser-based chat. Verify with
   `opencode --version`.
3. **Env vars** (already in `.env`, but flagged here because they affect the flow):
   - `OPENAI_API_KEY` — for the LLM provider
   - `LOCAL_EMBEDDING_MODEL_PATH` — for the embedding server
   - `KB_API_PORT` (default `8765`)
   - `OPENCODE_URL` (default `http://127.0.0.1:4096`)
4. **Tools**: `curl` and `jq`.

Set this once in your demo terminal so curl examples stay short:

```bash
export API=http://127.0.0.1:8765
```

---

## 1. Create a CaseStudy

```bash
curl -s -X POST $API/case-study \
  -H 'content-type: application/json' \
  -d '{
        "title": "Cu via resistance spike on M3",
        "description": "Yield drop on lot ABC123; statistical scorer flagged Tool-7 etch chamber",
        "defect_type": "electrical_open",
        "process_module": "BEOL",
        "scan_stage": "M3_etch"
      }' | jq .
```

Capture the `resource_id`:

```bash
CASE_ID=$(curl -s -X POST $API/case-study \
  -H 'content-type: application/json' \
  -d '{"title":"Cu via resistance spike on M3","description":"Yield drop on lot ABC123","defect_type":"electrical_open","process_module":"BEOL","scan_stage":"M3_etch"}' \
  | jq -r .resource_id)
echo "CASE_ID=$CASE_ID"
```

---

## 2. Open the workspace (first time)

```bash
curl -s -X POST $API/case-study/$CASE_ID/open-workspace | jq .
```

Expected response (note `resumed: false`):

```json
{
  "session_id": "...",
  "opencode_session_id": "ses_xxxx",
  "opencode_url": "http://127.0.0.1:4096/app?session=ses_xxxx",
  "workspace_path": "/.../active_sessions/<CASE_ID>",
  "resumed": false
}
```

Capture for later:

```bash
RESP=$(curl -s -X POST $API/case-study/$CASE_ID/open-workspace)
SESSION_ID=$(echo "$RESP" | jq -r .session_id)
OPENCODE_URL=$(echo "$RESP" | jq -r .opencode_url)
echo "SESSION_ID=$SESSION_ID"
echo "OPENCODE_URL=$OPENCODE_URL"
```

Verify the workspace was seeded:

```bash
ls active_sessions/$CASE_ID
# → AGENTS.md, CASE.md (rendered with the case title), and template files
```

---

## 3. Chat with the agent

Open `$OPENCODE_URL` in a browser. Send a message — anything that exercises
the RCA flow, e.g.:

> Tool-7 etch chamber correlates with the M3 via resistance spike. Is there
> a known mechanism that links chamber-to-chamber etch variation to Cu via
> opens at M3?

The agent will use the kb-mcp tools (recall) against the cognee KB to answer.
Send 2–3 messages so the resume step (§5) has visible chat history to verify.

---

## 4. Soft-close

Soft-close tars the workspace into `CaseStudy.workspace_archive`, removes the
active dir, marks the session `closed`, and **preserves** the opencode session
in opencode's SQLite (so chat history survives for resume).

```bash
curl -s -X POST $API/session/$SESSION_ID/soft-close | jq .
# → {"status":"closed","session_id":"..."}

ls active_sessions/$CASE_ID 2>/dev/null || echo "active dir removed ✓"
```

---

## 5. Resume — re-open the same case

```bash
RESUMED_RESP=$(curl -s -X POST $API/case-study/$CASE_ID/open-workspace)
echo "$RESUMED_RESP" | jq .
```

Confirm:
- `resumed: true`
- `opencode_session_id` matches the value from step 2
- `workspace_path` exists again, with files restored from `workspace_archive`

```bash
NEW_SESSION_ID=$(echo "$RESUMED_RESP" | jq -r .session_id)
RESUMED_URL=$(echo "$RESUMED_RESP" | jq -r .opencode_url)
echo "NEW_SESSION_ID=$NEW_SESSION_ID"
```

**Visual proof** — open `$RESUMED_URL` in the browser. The chat history from
step 3 should still be there. That's the load-bearing resume contract.

---

## 6. Upload the final report

User writes their RCA report locally as markdown, then uploads it. The API
writes it to the active workspace as `uploaded_final_report.md` and returns
the opencode URL so the user can review with the agent before finalizing.

```bash
cat > /tmp/final_report.md <<'EOF'
# Final RCA — Cu via resistance spike on M3

**Root cause:** Tool-7 etch chamber A wall conditioning drift caused
incomplete via clearing → residual barrier metal → high contact resistance.

**Evidence:**
- Tool-7 chamber A processed 87% of failing wafers
- Chamber B (same recipe, same week) had 0 failures
- Wall conditioning log shows missed PM cycle on 2026-04-22
EOF

curl -s -X POST $API/case-study/$CASE_ID/upload-final-report \
  -F "file=@/tmp/final_report.md;type=text/markdown" | jq .
```

Verify the file landed:

```bash
cat active_sessions/$CASE_ID/uploaded_final_report.md
```

---

## 7. Finalize (hard close)

Same as soft-close, **but** also permanently deletes the opencode session
(chat history gone) and triggers digest of the transcript into cognee.

```bash
curl -s -X POST $API/session/$NEW_SESSION_ID/finalize | jq .
# → {"status":"finalized","session_id":"..."}
```

Verify:
- Active dir removed: `ls active_sessions/$CASE_ID` → not found
- Session record closed with `inactivity_close_reason="finalize"`:
  ```bash
  curl -s $API/session/$NEW_SESSION_ID | jq '.data | {status, inactivity_close_reason, digested_at}'
  ```

---

## 8. Stale-case notification

A case is "stale" when `status=active` AND created > 7 days ago AND no agreed
RCAReport. The case we just made is brand-new, so the sweep finds nothing —
inject a backdated case to actually trigger notification.

```bash
# Inject an 8-day-old active case directly via the autocrud manager
uv run python -c "
import datetime as dt
from rca.container import container
from rca.domain.case_study import CaseStudy
ac = container.autocrud()
old = dt.datetime.now(dt.UTC) - dt.timedelta(days=8)
rev = ac.case_study_mgr().create(
    CaseStudy(title='Old neglected case', description='backdated for stale-notify demo'),
    user='demo', now=old,
)
print('STALE_CASE_ID=' + rev.resource_id)
"
```

List stale cases:

```bash
curl -s $API/admin/stale-cases | jq .
# → [{"case_id":"...","title":"Old neglected case","created_time":"2026-04-22T...","last_stale_notify_at":null}]
```

Trigger the sweep:

```bash
curl -s -X POST $API/admin/notify-stale-cases | jq .
# → {"notified": 1}
```

Verify dedup — re-run the sweep within 3 days, count should be 0:

```bash
curl -s -X POST $API/admin/notify-stale-cases | jq .
# → {"notified": 0}
```

Confirm `last_stale_notify_at` was stamped on the case:

```bash
curl -s $API/admin/stale-cases | jq '.[] | {case_id, last_stale_notify_at}'
```

Watch the KB API log (the terminal running `demo.sh`) for the WARNING line:

```
WARNING ... STALE CASE: case=... title='Old neglected case' — no agreed report after 8 days. ...
```

---

## Cleanup

```bash
rm -rf data/autocrud data/opencode_data active_sessions transcripts
```

Re-run from §1 with a clean slate.
