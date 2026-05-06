# rca-ui

NiceGUI chat + OpenAI Agents SDK driving the RCA agent. Replaces the
opencode + OpenChamber stack.

## Process model

Single Python process. Runs alongside `kb-api` (separate process, same
host or different). Talks to:

- `kb-api` over HTTP for knowledge operations (remember / recall / etc.).
- 4 stdio MCP subprocesses for the agent's tools:
    - `@modelcontextprotocol/server-filesystem` (workspace-scoped IO)
    - `kb-mcp` (knowledge graph, owned by the kb-api package)
    - `wafer-data-mcp` (fab data, ships in this package)
    - `stats-algo-mcp` (statistics, ships in this package)

## Data model

Cases live as directories under `<workspace_root>/<case_id>/`:

| File | Owner |
|---|---|
| `case.json` | UI (authoritative metadata) |
| `CASE.md` | auto-rendered from `case.json` |
| `notes.md` | agent + user |
| `draft_report.md` | agent + user |
| `transcript.jsonl` | session_store (append-only) |
| `session.json` | session_store (current state) |

The UI's index page enumerates cases by listing this directory; kb-api
is never asked.

## Run

`uv run rca-ui`. Default port 3001. Configure via the workspace-root `.env`
(`RCA_UI_PORT`, `KB_API_BASE_URL`, `RCA_UI_LLM_MODEL`, `OPENAI_API_KEY`).
