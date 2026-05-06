#!/usr/bin/env bash
# Demo bootstrap for the NiceGUI + OpenAI Agents SDK stack — replaces
# scripts/demo.sh's opencode + OpenChamber path.
#
# Boots:
#   - embedding-server (if EMBEDDING_PROVIDER=openai_compatible)
#   - kb-api  (FastAPI / 8765)
#   - rca-ui  (NiceGUI / 3001) — talks to kb-api over HTTP, spawns four
#     stdio MCPs for the agent: filesystem (npx, opensource), kb-mcp,
#     wafer-data-mcp, stats-algo-mcp.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "ERROR: .env missing. Copy .env.example to .env and set OPENAI_API_KEY (or ANTHROPIC_API_KEY)." >&2
  exit 1
fi

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
UI_HOST=${RCA_UI_HOST:-127.0.0.1}
UI_PORT=${RCA_UI_PORT:-3001}
UI_URL="http://${UI_HOST}:${UI_PORT}"

echo "[1/6] uv sync"
uv sync

echo "[2/6] generating mock fab data"
uv run python data/mock-fab-data/generate.py

EMB_PID=""
EMB_LOG=""
if [ "$EMB_PROVIDER" = "openai_compatible" ]; then
  if [ -z "${LOCAL_EMBEDDING_MODEL_PATH:-}" ]; then
    echo "ABORT: EMBEDDING_PROVIDER=openai_compatible but LOCAL_EMBEDDING_MODEL_PATH is empty." >&2
    exit 1
  fi
  echo "[3/6] starting embedding-server in the background"
  EMB_LOG=$(mktemp -t embedding-server.XXXXXX.log)
  echo "      log: $EMB_LOG"
  uv run embedding-server >"$EMB_LOG" 2>&1 &
  EMB_PID=$!
  echo "      waiting for /health on $EMB_URL ..."
  for i in $(seq 1 120); do
    if curl -fs "$EMB_URL/health" >/dev/null 2>&1; then
      echo "      embedding-server up (after ${i}s)"
      break
    fi
    if ! kill -0 "$EMB_PID" 2>/dev/null; then
      echo "ERROR: embedding-server died." >&2
      tail -n 50 "$EMB_LOG" >&2
      exit 1
    fi
    sleep 1
  done
else
  echo "[3/6] EMBEDDING_PROVIDER=$EMB_PROVIDER → skipping embedding-server"
fi

echo "[4/6] starting KB API in the background"
KB_LOG=$(mktemp -t kb-api.XXXXXX.log)
echo "      log: $KB_LOG"
uv run kb-api >"$KB_LOG" 2>&1 &
API_PID=$!

UI_PID=""
UI_LOG=""
TAIL_PID=""

kill_tree() {
  local pid=$1 sig=${2:-TERM}
  [ -z "$pid" ] && return 0
  kill -0 "$pid" 2>/dev/null || return 0
  local children
  children=$(pgrep -P "$pid" 2>/dev/null || true)
  kill -"$sig" "$pid" 2>/dev/null || true
  for c in $children; do
    kill_tree "$c" "$sig"
  done
}

cleanup() {
  printf '\n[demo-rca-ui.sh] signal received, cleanup invoked...\n' >&2
  trap - EXIT INT TERM TSTP
  for pid in "$API_PID" "$UI_PID" "$EMB_PID" "$TAIL_PID"; do
    kill_tree "$pid" TERM
  done
  sleep 1
  for pid in "$API_PID" "$UI_PID" "$EMB_PID" "$TAIL_PID"; do
    kill_tree "$pid" KILL
  done
  "$(dirname "$0")/kill-stale.sh" >/dev/null 2>&1 || true
  printf '[demo-rca-ui.sh] done.\n' >&2
}
trap 'cleanup; exit 146' TSTP
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM
trap cleanup EXIT

echo "      waiting for /health on $API_URL ..."
for i in $(seq 1 60); do
  if curl -fs "$API_URL/health" >/dev/null 2>&1; then
    echo "      KB API is up (after ${i}s)"
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "ERROR: KB API died during startup." >&2
    tail -n 50 "$KB_LOG" >&2
    exit 1
  fi
  sleep 1
done

echo "[5/6] starting rca-ui (NiceGUI + OpenAI Agents SDK) in the background"
UI_LOG=$(mktemp -t rca-ui.XXXXXX.log)
echo "      log: $UI_LOG"
echo "      url: $UI_URL"
uv run rca-ui >"$UI_LOG" 2>&1 &
UI_PID=$!

echo "      waiting for / on $UI_URL ..."
for i in $(seq 1 60); do
  if curl -fs -o /dev/null "$UI_URL/" 2>/dev/null; then
    echo "      rca-ui up (after ${i}s)"
    break
  fi
  if ! kill -0 "$UI_PID" 2>/dev/null; then
    echo "ERROR: rca-ui died during startup. Last 80 lines of log:" >&2
    tail -n 80 "$UI_LOG" >&2
    exit 1
  fi
  sleep 1
done

if [ "${SKIP_PRIMER:-0}" = "1" ]; then
  echo "[6/6] SKIP_PRIMER=1 → skipping primer seed"
else
  echo "[6/6] seeding KB with built-in semiconductor primer"
  uv run python scripts/seed_primer.py
fi

echo
echo "  ┌─ ready ─────────────────────────────────────────"
echo "  │ kb-api : $API_URL"
echo "  │ rca-ui : $UI_URL  ← open this in a browser"
echo "  └──────────────────────────────────────────────────"
echo

if [ -n "$EMB_LOG" ]; then echo "  (embedding-server log: $EMB_LOG)"; fi
echo "  (kb-api log: $KB_LOG)"
echo "  (rca-ui log: $UI_LOG)"
echo
echo "Following kb-api log (Ctrl-C or Ctrl-Z to stop):"
tail -f "$KB_LOG" &
TAIL_PID=$!
wait "$TAIL_PID" 2>/dev/null || true
