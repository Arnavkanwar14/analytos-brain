#!/usr/bin/env bash
set -euo pipefail

ROOT=/root/analytos-brain
cd "$ROOT"

# Hugging Face Spaces exposes one public port. Keep OG internal (8080) and expose
# FastAPI at 7860; FastAPI becomes the single external route for dashboard + HITL API.
export OMNIGRAPH_BASE_URL="${OMNIGRAPH_BASE_URL:-http://127.0.0.1:8080}"
export OMNIGRAPH_BIND="${OMNIGRAPH_BIND:-127.0.0.1:8080}"
export HF_PORT="${PORT:-7860}"
export PATH="/root/.local/bin:${PATH}"

# Ensure Omnigraph binaries exist in container runtime.
if ! command -v omnigraph >/dev/null 2>&1 || ! command -v omnigraph-server >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/ModernRelay/omnigraph/main/scripts/install.sh | bash
  export PATH="/root/.local/bin:${PATH}"
fi

# Ephemeral container bootstrap: create/refresh .env and re-apply cluster state.
python3 scripts/gen_env.py
python3 scripts/apply_cluster.py

# Start omnigraph-server in background, then seed main if empty (golden, no LLM).
python3 scripts/start_server.py &
OG_PID=$!
sleep 3
python3 scripts/bootstrap_if_empty.py || true

cleanup() {
  kill "$OG_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

exec uvicorn backend.app:app --host 0.0.0.0 --port "$HF_PORT"
