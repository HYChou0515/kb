#!/usr/bin/env bash
# Demo bootstrap — runs everything except OpenCode itself.
#
# Prereqs:
#   - uv installed
#   - .env exists with OPENAI_API_KEY (or ANTHROPIC_API_KEY if LLM_PROVIDER=anthropic)
#   - if EMBEDDING_PROVIDER=openai_compatible (the default), LOCAL_EMBEDDING_MODEL_PATH
#     must point to your locally-downloaded sentence-transformers checkpoint.
#   - if OPENCHAMBER_BASE_URL is set, the `openchamber` CLI must be on PATH
#     (https://github.com/btriapitsyn/openchamber).
#
# What it does:
#   1. uv sync
#   2. sanity-check LLM key
#   3. generate mock fab data
#   4. (if local embeddings) start embedding-server in background
#   5. start KB API in background
#   6. (if OPENCHAMBER_BASE_URL set) start OpenChamber in background
#   7. seed KB with primer
#   8. tail KB API log (Ctrl-C to stop)
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

echo "[5/8] starting KB API in the background"
KB_LOG=$(mktemp -t kb-api.XXXXXX.log)
echo "      log: $KB_LOG"
uv run kb-api >"$KB_LOG" 2>&1 &
API_PID=$!

OC_PID=""
OC_LOG=""

# `uv run` → uvicorn → kb-api → opencode child → MCP servers is a 4-deep
# process tree, and `kill <pid>` only signals the direct child. Walk the
# tree via pgrep so SIGTERM reaches all descendants (then SIGKILL whoever
# didn't go down). Without this, Ctrl-C leaves opencode + MCP processes
# running and the next demo.sh fails with "address already in use".
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
  trap - EXIT INT TERM  # don't re-enter on signal during cleanup
  for pid in "$API_PID" "$OC_PID" "$EMB_PID"; do
    kill_tree "$pid" TERM
  done
  # Brief grace, then SIGKILL anything that ignored TERM.
  sleep 1
  for pid in "$API_PID" "$OC_PID" "$EMB_PID"; do
    kill_tree "$pid" KILL
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

# OpenChamber attaches to the opencode server kb-api spawns. We start it
# here so the URL kb-api hands back (when OPENCHAMBER_BASE_URL is set) is
# already live by the time the user follows it. opencode itself is started
# lazily by kb-api on the first /open-workspace call — OpenChamber will
# show a "waiting for opencode" state until then, which is fine.
if [ -n "${OPENCHAMBER_BASE_URL:-}" ]; then
  if ! command -v openchamber >/dev/null 2>&1; then
    echo "ERROR: OPENCHAMBER_BASE_URL is set but \`openchamber\` is not on PATH." >&2
    echo "       Install per upstream instructions at https://github.com/openchamber/openchamber" >&2
    echo "       Or unset OPENCHAMBER_BASE_URL to fall back to opencode's built-in /app." >&2
    exit 1
  fi
  OC_PORT=${OPENCHAMBER_PORT:-3000}
  OC_LOG=$(mktemp -t openchamber.XXXXXX.log)
  # Match the port kb-api spawns opencode on. Settings reads OPENCODE_URL
  # from .env (default http://127.0.0.1:4096); when unset we fall back to
  # opencode's compiled-in default port. ${var##*:} = strip everything up
  # to and including the last ':' → just the port.
  OPENCODE_URL_VAL=${OPENCODE_URL:-http://127.0.0.1:4096}
  OPENCODE_PORT_VAL=${OPENCODE_URL_VAL##*:}

  # Project-local data dir for OpenChamber so we don't pollute the user's
  # global ~/.config/openchamber. Mirrors the XDG isolation we do for
  # opencode (see local_subprocess.py: opencode_data_root).
  OC_DATA_DIR=${OPENCHAMBER_DATA_DIR:-$PWD/data/openchamber}

  # OpenChamber's UI doesn't read opencode's config.model — it reads its own
  # settings.json:defaultModel. Without seeding it, the UI shows the
  # hardcoded fallback "opencode/big-pickle" no matter what we configure
  # opencode-side. Match the fallback chain in src/rca/config.py: prefer
  # OPENCODE_LLM_*, else LLM_*.
  CHAMBER_PROVIDER=${OPENCODE_LLM_PROVIDER:-${LLM_PROVIDER:-openai}}
  CHAMBER_MODEL=${OPENCODE_LLM_MODEL:-${LLM_MODEL:-gpt-4o}}
  CHAMBER_DEFAULT_MODEL="${CHAMBER_PROVIDER}/${CHAMBER_MODEL}"
  mkdir -p "$OC_DATA_DIR"
  CHAMBER_DEFAULT_MODEL="$CHAMBER_DEFAULT_MODEL" \
  OC_SETTINGS_PATH="$OC_DATA_DIR/settings.json" \
  python3 - <<'PY'
import json, os, pathlib
path = pathlib.Path(os.environ["OC_SETTINGS_PATH"])
target_model = os.environ["CHAMBER_DEFAULT_MODEL"]
try:
    current = json.loads(path.read_text("utf-8")) if path.exists() else {}
    if not isinstance(current, dict):
        current = {}
except (json.JSONDecodeError, OSError):
    current = {}
current["defaultModel"] = target_model
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(current, indent=2), "utf-8")
print(f"      settings.json defaultModel ← {target_model}")
PY

  echo "[6/8] starting OpenChamber in the background"
  echo "      log:      $OC_LOG"
  echo "      data dir: $OC_DATA_DIR"
  echo "      port:     $OC_PORT (attaches to opencode at port $OPENCODE_PORT_VAL)"
  OC_ARGS=(--port "$OC_PORT" --foreground)
  if [ -n "${OPENCHAMBER_UI_PASSWORD:-}" ]; then
    OC_ARGS+=(--ui-password "$OPENCHAMBER_UI_PASSWORD")
  fi
  OPENCODE_PORT="$OPENCODE_PORT_VAL" \
  OPENCODE_SKIP_START=true \
  OPENCHAMBER_DATA_DIR="$OC_DATA_DIR" \
    openchamber "${OC_ARGS[@]}" >"$OC_LOG" 2>&1 &
  OC_PID=$!
  echo "      waiting for $OPENCHAMBER_BASE_URL ..."
  for i in $(seq 1 30); do
    if curl -fs -o /dev/null "$OPENCHAMBER_BASE_URL/" 2>/dev/null; then
      echo "      OpenChamber is up (after ${i}s)"
      break
    fi
    if ! kill -0 "$OC_PID" 2>/dev/null; then
      echo "ERROR: OpenChamber died during startup. Last 50 lines of log:" >&2
      tail -n 50 "$OC_LOG" >&2
      exit 1
    fi
    sleep 1
  done
else
  echo "[6/8] OPENCHAMBER_BASE_URL not set → using opencode's built-in /app"
fi

if [ "${SKIP_PRIMER:-0}" = "1" ]; then
  echo "[7/8] SKIP_PRIMER=1 → skipping primer seed"
else
  echo "[7/8] seeding KB with built-in semiconductor primer"
  uv run python scripts/seed_primer.py
fi

echo "[8/8] following KB API log (Ctrl-C to stop)"
if [ -n "$EMB_LOG" ]; then
  echo "      (embedding-server log at $EMB_LOG)"
fi
if [ -n "$OC_LOG" ]; then
  echo "      (openchamber log at $OC_LOG)"
fi
tail -f "$KB_LOG"
