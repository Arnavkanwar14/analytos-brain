#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[startup] %s\n' "$*"
}

print_log_excerpt() {
  local path="$1"
  python3 - "$path" <<'PY2'
from pathlib import Path
import sys
p = Path(sys.argv[1])
if not p.exists():
    print('[startup] log file not found:', p)
    raise SystemExit(0)
lines = p.read_text(errors='replace').splitlines()
for line in lines[-40:]:
    print(line)
PY2
}

ROOT=/root/analytos-brain
cd "$ROOT"

export OMNIGRAPH_BASE_URL="${OMNIGRAPH_BASE_URL:-http://127.0.0.1:8080}"
export OMNIGRAPH_BIND="${OMNIGRAPH_BIND:-127.0.0.1:8080}"
export HF_PORT="${PORT:-7860}"
export PATH="/root/.local/bin:${PATH}"

OMNIGRAPH_HEALTH_TIMEOUT_SECS="${OMNIGRAPH_HEALTH_TIMEOUT_SECS:-45}"
BOOTSTRAP_TIMEOUT_SECS="${BOOTSTRAP_TIMEOUT_SECS:-120}"
OMNIGRAPH_LOG_FILE="${OMNIGRAPH_LOG_FILE:-/tmp/omnigraph-server.log}"

cleanup() {
  if [[ -n "${OG_PID:-}" ]] && kill -0 "$OG_PID" >/dev/null 2>&1; then
    log "stopping omnigraph-server pid=$OG_PID"
    kill "$OG_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

log "startup script initialized"
log "cwd=$ROOT"
log "PORT=$HF_PORT OMNIGRAPH_BASE_URL=$OMNIGRAPH_BASE_URL"

for cmd in python3 curl omnigraph omnigraph-server timeout; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "ERROR missing required command: $cmd"
    exit 1
  fi
done

log "generating .env"
python3 scripts/gen_env.py

log "applying cluster config"
python3 scripts/apply_cluster.py

log "starting omnigraph sidecar"
python3 scripts/start_server.py >"$OMNIGRAPH_LOG_FILE" 2>&1 &
OG_PID=$!
log "omnigraph sidecar pid=$OG_PID log=$OMNIGRAPH_LOG_FILE"

log "waiting for omnigraph health (timeout=${OMNIGRAPH_HEALTH_TIMEOUT_SECS}s)"
READY=0
for ((i=1; i<=OMNIGRAPH_HEALTH_TIMEOUT_SECS; i++)); do
  if ! kill -0 "$OG_PID" >/dev/null 2>&1; then
    log "ERROR omnigraph sidecar exited before becoming healthy"
    print_log_excerpt "$OMNIGRAPH_LOG_FILE"
    exit 1
  fi

  if curl -fsS --max-time 2 "$OMNIGRAPH_BASE_URL/healthz" >/dev/null 2>&1; then
    READY=1
    break
  fi

  if (( i % 5 == 0 )); then
    log "still waiting for omnigraph health... (${i}s)"
  fi
  sleep 1
done

if [[ "$READY" -ne 1 ]]; then
  log "ERROR omnigraph health check timed out"
  print_log_excerpt "$OMNIGRAPH_LOG_FILE"
  exit 1
fi
log "omnigraph sidecar healthy"

log "running bootstrap-if-empty (timeout=${BOOTSTRAP_TIMEOUT_SECS}s)"
if ! timeout "$BOOTSTRAP_TIMEOUT_SECS" python3 scripts/bootstrap_if_empty.py; then
  log "bootstrap step timed out or failed; continuing startup"
fi

log "starting FastAPI server"
exec python3 -m uvicorn backend.app:app --host 0.0.0.0 --port "$HF_PORT"
