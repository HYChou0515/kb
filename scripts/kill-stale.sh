#!/usr/bin/env bash
# Kill leftover kb-api / opencode / openchamber / MCP-server processes plus
# anything still listening on the demo ports. Robust against the script's own
# shell appearing in the pgrep matches (its cmdline contains the patterns).

set -u

self_pid=$$
self_ppid=${PPID:-0}

kill_match() {
  local pattern=$1 sig=${2:-TERM}
  pgrep -f "$pattern" 2>/dev/null | while read -r pid; do
    [ "$pid" = "$self_pid" ] && continue
    [ "$pid" = "$self_ppid" ] && continue
    kill -"$sig" "$pid" 2>/dev/null || true
  done
}

PATTERNS=(
  '\.venv/bin/kb-api'
  'opencode serve --port'
  'openchamber.*--port'
  'uv run kb-mcp'
  'uv run wafer-data-mcp'
  'uv run stats-algo-mcp'
)

for pat in "${PATTERNS[@]}"; do kill_match "$pat" TERM; done
sleep 1
for pat in "${PATTERNS[@]}"; do kill_match "$pat" KILL; done

# Backstop: anything still bound to a demo port gets KILLed by PID.
for port in 8765 4096 3000; do
  pids=$(ss -tlnp 2>/dev/null \
    | awk -v p=":$port" '$0 ~ p' \
    | grep -oP 'pid=\K[0-9]+' || true)
  for pid in $pids; do
    [ "$pid" = "$self_pid" ] && continue
    [ "$pid" = "$self_ppid" ] && continue
    kill -KILL "$pid" 2>/dev/null || true
  done
done

# OpenChamber's "am I already running?" check reads run/openchamber-<port>.pid
# and asks ps if that PID is alive. If a previous demo.sh died unclean and
# the node process became a zombie (parent didn't reap it), the PID is still
# in `ps` (state "Z") and OpenChamber refuses to start with "already running
# on port 3000". Killing the zombie doesn't help — only its parent can reap
# it. The pid file IS our problem; nuke it.
project_root=$(dirname "$(dirname "$(readlink -f "$0")")")
rm -f "$project_root"/data/openchamber/run/openchamber-*.pid \
      "$project_root"/data/openchamber/run/openchamber-*.json 2>/dev/null || true

remaining=$(ss -tlnp 2>/dev/null | grep -cE ':8765 |:4096 |:3000 ' || true)
if [ "$remaining" -eq 0 ]; then
  echo "stale processes cleared (ports 8765 / 4096 / 3000 free)"
else
  echo "WARNING: some demo-port listeners still alive:"
  ss -tlnp 2>/dev/null | grep -E ':8765 |:4096 |:3000 ' >&2
  exit 1
fi
