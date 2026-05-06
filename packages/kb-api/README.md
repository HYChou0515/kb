# kb-api

Thin HTTP wrapper over [cognee](https://www.cognee.ai/) v1. Five routes:

| Route | Action |
|---|---|
| `POST /remember` | `cognee.remember(text, dataset_name=…, self_improvement=…)` |
| `POST /recall` | `cognee.recall(query, datasets=…, top_k=…)` |
| `POST /search` | `cognee.search(query, query_type=…, datasets=…)` |
| `POST /improve` | `cognee.improve(dataset, …)` (cognee v1's "new cognify") |
| `DELETE /forget` | `cognee.forget(data_id|dataset|everything)` |

Plus `GET /health`.

Trust-tier signal: encoded in `dataset_name` — `"rca_reports"` (top),
`"rca_conversations"` (mid), `"rca_literature"` (baseline).

Run: `uv run kb-api`. Configure via `.env` at the workspace root.

The companion `kb-mcp` console script exposes the same five primitives
over MCP stdio (used by external agents and by `rca-ui`'s in-process agent).
