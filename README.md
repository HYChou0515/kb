# RCA Knowledge POC

Semiconductor defect root-cause analysis (RCA) POC: a **conversational agent**
that runs in [OpenCode](https://github.com/sst/opencode) and uses a
domain-specific **knowledge base** (built on [Cognee](https://github.com/topoteretes/cognee)
+ Claude Sonnet 4.5) to **filter false alarms** out of an in-house statistical
correlation scorer.

## The problem we're solving

Fab data is high-dimensional (many tools × many steps × many parameters) and
low-N (few wafers per case). The in-house statistics algorithm dutifully
flags everything that correlates — and over-generates **false alarms** that
look real but have no physical mechanism.

This system filters those candidates by asking, for each one:
> Is there a **plausible causal mechanism** in the semiconductor knowledge
> base that connects this factor to this defect?

Candidates with no mechanism in the graph get dropped. Candidates with a
mechanism + supporting citations survive into the engineer's hypothesis list.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  OpenCode  (the user runs this in their terminal)       │
│   ↳ skill: opencode-skill/rca-agent.md                  │
└─────────────────────────────────────────────────────────┘
        │ MCP            │ MCP                │ MCP
        ▼                ▼                    ▼
 ┌─────────────┐  ┌────────────────┐  ┌─────────────────┐
 │  kb-mcp     │  │ wafer-data-mcp │  │ stats-algo-mcp  │
 │ (proxy)     │  │ (mock CSV)     │  │ (mock Pearson)  │
 └─────┬───────┘  └────────────────┘  └─────────────────┘
       │ HTTP
       ▼
 ┌──────────────────────────────────────────────────────┐
 │  KB API  (FastAPI)                                   │
 │   POST /retain/text                                  │
 │   POST /retain/file                                  │
 │   POST /retain/extraction   ← pre-extracted JSON in  │
 │   POST /retain/conversation ← extract from chat in   │
 │   POST /recall   (mode = snippets|assessment|        │
 │                          synthesis)                  │
 │                                                      │
 │   Cognee + Claude Sonnet 4.5 + kuzu + LanceDB    │
 └──────────────────────────────────────────────────────┘
```

## What's in the box

| Path | Purpose |
|---|---|
| `src/kb_api/` | FastAPI service (the KB API) |
| `src/rca_knowledge/` | Core: extractor, cognee client, ingestion pipeline, causal reasoner |
| `src/mcp_servers/` | Three MCP servers (kb / wafer-data / stats-algo) |
| `opencode-skill/rca-agent.md` | System prompt driving the 9-step RCA flow |
| `opencode-skill/mcp.json.example` | OpenCode MCP server config template |
| `data/mock-fab-data/` | Mock wafer history + defect counts (with generator) |
| `data/sources/` | Drop semiconductor PDFs / texts here to seed the KB |
| `data/benchmark/test_cases.yaml` | Sanity-check causal queries |
| `scripts/` | Dev-only CLIs (ingest / query / run_benchmark) — not the main entry |

## Quickstart (POC demo path)

### 0. Install
```bash
cd rca-knowledge-poc
uv sync
cp .env.example .env
# edit .env:
#   default LLM_PROVIDER=openai → set OPENAI_API_KEY=sk-...
#   or LLM_PROVIDER=anthropic   → set ANTHROPIC_API_KEY=sk-ant-...
```

### LLM provider switch
Both extraction and reasoning go through `src/rca_knowledge/llm.py`, which
picks Anthropic or OpenAI based on `LLM_PROVIDER`. Defaults:

| Provider | Default model | Override env |
|---|---|---|
| `openai` (default) | `gpt-4o` | `LLM_MODEL`, optional `EXTRACTION_MODEL` / `REASONING_MODEL` |
| `anthropic` | `claude-sonnet-4-5` | same |

Cognee internally uses LiteLLM and reads the same `LLM_PROVIDER` /
`LLM_MODEL` / `LLM_API_KEY` vars, so switching `LLM_PROVIDER` flips both
the KB's own LLM calls *and* cognee's pipeline LLM in one shot.

### Embeddings — local sentence-transformers, no HuggingFace required
`src/embedding_server/` is a small FastAPI app that wraps any local
sentence-transformers checkpoint behind an OpenAI-compatible
`/v1/embeddings` endpoint. cognee then talks to it via
`EMBEDDING_PROVIDER=openai_compatible`. This is the **default** path for
this POC because most fab networks block HuggingFace.

```bash
# 1. point .env at your local checkpoint
LOCAL_EMBEDDING_MODEL_PATH=/opt/models/qwen3-embedding-0.6B
EMBEDDING_DIMENSIONS=1024     # match the model's actual dim

# 2. demo.sh starts the embedding-server automatically before the KB API
./scripts/demo.sh
```

If your environment *does* have HuggingFace access, comment option (A) and
uncomment option (B) in `.env.example` to use cognee's bundled `fastembed`
engine — no separate process needed.

### 1. Generate the mock fab data
```bash
uv run python data/mock-fab-data/generate.py
```

### 2. Seed the knowledge base
Drop a few semiconductor PDFs / text files into `data/sources/` and ingest
them once (this is the expensive Claude extraction step):

```bash
# Start the KB API in one terminal
uv run kb-api

# In another terminal, push some content
curl -X POST http://127.0.0.1:8765/retain/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Particle contamination during via etch can leave residue on M2 line edges, creating shorts between adjacent metal lines after CMP. Common sources: chamber wall flaking, polymer accumulation, electrode erosion.", "label": "via-etch-particle-mechanism"}'

# Or via dev CLI
uv run python scripts/ingest.py --file data/sources/some_paper.pdf
```

### 3. Wire OpenCode to the MCP servers
Copy `opencode-skill/mcp.json.example` to your OpenCode config location, edit
`cwd` to the absolute path, and load `opencode-skill/rca-agent.md` as a skill.

### 4. Run the RCA agent in OpenCode
Start a session and say something like:
> "I want to RCA a metal_short_M2 issue."

The agent will walk you through steps 1–9, fetch the mock data, run the
stats algo (which produces lots of false alarms), and use the KB to filter
them down to the one or two candidates with a real mechanism. It should
land on `M2_VIA_ETCH × ETCH_C` (the true root cause baked into the mock data).

## API reference

All endpoints are POST unless noted.

| Endpoint | Body | Notes |
|---|---|---|
| `GET /health` | — | liveness check |
| `/retain/text` | `{text, label, source_kind?, cognify?}` | KB runs Claude extraction internally |
| `/retain/file` | multipart `file=...` | PDF / TXT / MD |
| `/retain/extraction` | `{extraction: ExtractionResult, source_label, source_kind?}` | **★ pre-extracted JSON; no internal LLM call** |
| `/retain/conversation` | `{messages: [{role,content}], session_id?}` | **★ extracts from chat; useful for RCA session learning** |
| `/recall` | `{query, mode, process_context?, source_filter?, top_k?}` | mode = `snippets` / `assessment` / `synthesis` |
| `/admin/cognify` | `{dataset?}` | trigger graph build |
| `/admin/prune` (DELETE) | — | wipe stores (POC only) |

`source_kind`: `literature` (default) or `conversation` — determines the
`node_set` so retrieval can filter by source.

`source_filter`: `all` (default) / `literature` / `conversations`.

## Recall modes

| `mode` | Returns | Cost |
|---|---|---|
| `snippets` | Raw KG snippets, no LLM synthesis | cheap |
| `assessment` | `CausalAssessment` (verdict + mechanisms + confounders + citations + suggested_investigations + knowledge_gaps) — **default** | one Claude call |
| `synthesis` | Prose synthesis via cognee `GRAPH_COMPLETION` | one Claude call |

The OpenCode agent uses `assessment` for step 8 filtering, `snippets` when
the user pushes back and wants to see the raw evidence, and `synthesis` for
step 9 report prose.

## Custom semiconductor extraction

`src/rca_knowledge/ingestion/extractor.py` defines a domain-specific Claude
prompt that turns text into a strict JSON `ExtractionResult` with:

- **Entities** typed as: process_step / material / defect_type / mechanism /
  process_parameter / measurement_metric / equipment / layer_or_module / other
- **Relations** typed as: causes / inhibits / correlates_with / is_a /
  part_of / measured_by / occurs_in / produced_by / **confounded_by**
- **Confidence** per relation: established_physics / empirically_observed /
  theoretical_or_proposed
- **Mechanism** field (1-2 sentence physical/chemical explanation, **required**
  for any `causes` relation)

This schema is what `/retain/extraction` accepts when an external system
(e.g. another team's GPT-4o pipeline) feeds you pre-distilled knowledge.

## Mock data design

`data/mock-fab-data/generate.py` produces deterministic CSVs with:

- 50 wafers across 5 lots
- 20 process steps (incl. 2 dummy/scribe steps the user is expected to drop)
- True root cause: tool `ETCH_C` at step `M2_VIA_ETCH` (~3× defect count)
- Enough noise that ~10–30 spurious correlations show up — exactly the
  failure mode the KG filter is supposed to fix.

## Dev scripts (not the main demo path)

For developing the KB itself, without going through OpenCode:

```bash
uv run python scripts/ingest.py --file data/sources/foo.pdf
uv run python scripts/query.py --correlation "..." --context "..."
uv run python scripts/learn_from_chat.py --file path/to/session.json
uv run python scripts/run_benchmark.py
```

These import the modules directly (no API roundtrip). They exist for
extractor prompt iteration; production agents go through the API + MCP path.

## Design decisions

- **kuzu + LanceDB** in POC; swap to Neo4j by changing
  `GRAPH_DATABASE_PROVIDER` in `.env`.
- **OpenAI default, Anthropic optional.** Both extraction and reasoning go
  through one provider-agnostic client. Switch via `LLM_PROVIDER`. Different
  models per role available via `EXTRACTION_MODEL` / `REASONING_MODEL`.
- **Localhost only**, no auth — POC.
- **Stats algo is a mock** that deliberately over-produces false alarms.
  Replace with a real MCP wrapper around the in-house algorithm for
  production.
- **OpenCode chosen** because it's open-source and runs inside the customer's
  network. The MCP servers don't depend on OpenCode specifically — any MCP
  client (including Claude Code) works.

## What's intentionally NOT here

- No web UI
- No cloud deployment
- No authentication
- No retry logic on Claude API calls
- No real fab data integration (use the wafer-data-mcp interface as the contract for v2)
- No KG provenance versioning (re-extract = additive; manage by `prune` for now)
