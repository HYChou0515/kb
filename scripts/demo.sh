#!/usr/bin/env bash
# Demo bootstrap — runs everything except OpenCode itself.
#
# Prereqs:
#   - uv installed
#   - .env exists with OPENAI_API_KEY (or ANTHROPIC_API_KEY if LLM_PROVIDER=anthropic)
#   - if EMBEDDING_PROVIDER=openai_compatible (the default), LOCAL_EMBEDDING_MODEL_PATH
#     must point to your locally-downloaded sentence-transformers checkpoint.
#
# What it does:
#   1. uv sync
#   2. sanity-check LLM key
#   3. generate mock fab data
#   4. (if local embeddings) start embedding-server in background
#   5. start KB API in background
#   6. seed KB with primer
#   7. tail KB API log (Ctrl-C to stop)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "ERROR: .env missing. Copy .env.example to .env and set OPENAI_API_KEY (or ANTHROPIC_API_KEY)." >&2
  exit 1
fi

# Read enough .env to drive bootstrap decisions. We don't override anything that
# is already in the environment.
set -a
# shellcheck disable=SC1091
source .env
set +a

API_HOST=${KB_API_HOST:-127.0.0.1}
API_PORT=${KB_API_PORT:-8765}
API_URL="http://${API_HOST}:${API_PORT}"
EMB_HOST=${EMBEDDING_SERVER_HOST:-127.0.0.1}
EMB_PORT=${EMBEDDING_SERVER_PORT:-8766}
EMB_URL="http://${EMB_HOST}:${EMB_PORT}"
EMB_PROVIDER=${EMBEDDING_PROVIDER:-openai_compatible}

echo "[1/7] uv sync"
uv sync

echo "[2/7] sanity-checking LLM provider key (one tiny call)"
if ! uv run python scripts/check_llm.py; then
  echo "ABORT: LLM key sanity check failed. See messages above." >&2
  echo "       Fix .env, then re-run ./scripts/demo.sh" >&2
  exit 1
fi

echo "[3/7] generating mock fab data"
uv run python data/mock-fab-data/generate.py

EMB_PID=""
EMB_LOG=""
if [ "$EMB_PROVIDER" = "openai_compatible" ]; then
  if [ -z "${LOCAL_EMBEDDING_MODEL_PATH:-}" ]; then
    echo "ABORT: EMBEDDING_PROVIDER=openai_compatible but LOCAL_EMBEDDING_MODEL_PATH is empty." >&2
    echo "       Set LOCAL_EMBEDDING_MODEL_PATH in .env to your local sentence-transformers checkpoint dir," >&2
    echo "       or switch EMBEDDING_PROVIDER=fastembed (needs HuggingFace network access)." >&2
    exit 1
  fi
  if [ ! -d "$LOCAL_EMBEDDING_MODEL_PATH" ]; then
    echo "ABORT: LOCAL_EMBEDDING_MODEL_PATH does not exist: $LOCAL_EMBEDDING_MODEL_PATH" >&2
    exit 1
  fi

  echo "[4/7] starting embedding-server in the background"
  EMB_LOG=$(mktemp -t embedding-server.XXXXXX.log)
  echo "      log:   $EMB_LOG"
  echo "      model: $LOCAL_EMBEDDING_MODEL_PATH"
  uv run embedding-server >"$EMB_LOG" 2>&1 &
  EMB_PID=$!

  echo "      waiting for /health on $EMB_URL ..."
  for i in $(seq 1 120); do
    if curl -fs "$EMB_URL/health" >/dev/null 2>&1; then
      DIM=$(curl -fs "$EMB_URL/health" | python3 -c "import json,sys; print(json.load(sys.stdin).get('dim'))")
      echo "      embedding-server up (after ${i}s, dim=$DIM)"
      break
    fi
    if ! kill -0 "$EMB_PID" 2>/dev/null; then
      echo "ERROR: embedding-server died during startup. Last 50 lines of log:" >&2
      tail -n 50 "$EMB_LOG" >&2
      exit 1
    fi
    sleep 1
  done
else
  echo "[4/7] EMBEDDING_PROVIDER=$EMB_PROVIDER → skipping local embedding-server"
fi

echo "[5/7] starting KB API in the background"
KB_LOG=$(mktemp -t kb-api.XXXXXX.log)
echo "      log: $KB_LOG"
uv run kb-api >"$KB_LOG" 2>&1 &
API_PID=$!

cleanup() {
  for pid in "$API_PID" "$EMB_PID"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT INT TERM

echo "      waiting for /health on $API_URL ..."
for i in $(seq 1 60); do
  if curl -fs "$API_URL/health" >/dev/null 2>&1; then
    echo "      KB API is up (after ${i}s)"
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "ERROR: KB API died during startup. Last 50 lines of log:" >&2
    tail -n 50 "$KB_LOG" >&2
    exit 1
  fi
  sleep 1
done

echo "[6/7] seeding KB with built-in semiconductor primer"
uv run python scripts/seed_primer.py

echo "[7/7] following KB API log (Ctrl-C to stop)"
if [ -n "$EMB_LOG" ]; then
  echo "      (embedding-server log at $EMB_LOG)"
fi
tail -f "$KB_LOG"
