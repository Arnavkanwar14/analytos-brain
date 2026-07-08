#!/usr/bin/env bash
# Bake Omnigraph cluster state + golden seed graph into the Docker image.
set -euo pipefail
ROOT=/root/analytos-brain
cd "$ROOT"
export HF_SPACE=1
export OMNIGRAPH_BASE_URL="http://127.0.0.1:8080"
export OMNIGRAPH_BIND="127.0.0.1:8080"
export PATH="/root/.local/bin:${PATH}"

LOG=/tmp/omnigraph-bake.log
echo "[bake] starting omnigraph-server"
python3 scripts/start_server.py >"$LOG" 2>&1 &
OG_PID=$!
cleanup() { kill "$OG_PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "[bake] waiting for omnigraph health"
READY=0
for i in $(seq 1 45); do
  if ! kill -0 "$OG_PID" >/dev/null 2>&1; then
    echo "[bake] ERROR omnigraph exited early"
    tail -40 "$LOG" || true
    exit 1
  fi
  if curl -fsS --max-time 2 "$OMNIGRAPH_BASE_URL/healthz" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done
if [[ "$READY" -ne 1 ]]; then
  echo "[bake] ERROR omnigraph health timeout"
  tail -40 "$LOG" || true
  exit 1
fi

echo "[bake] seeding graph (golden bootstrap)"
python3 scripts/bootstrap_if_empty.py

touch "$ROOT/.hf-baked"
echo "[bake] done"
