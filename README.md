---
title: Analytos Brain
emoji: "🧠"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Analytos Brain on Omnigraph

POC for the Analytos Omnigraph assignment implementing:

`seed-data -> ingest branch -> diff/HITL -> approve/merge -> dashboard + MCP -> content/GTM agents`

## Architecture

- **Ingestion pipeline** (`pipeline/run.py`): extracts 5 seed docs into typed nodes/edges on `ingest/<run-id>` branches (never writes directly to `main`)
- **Governance/HITL** (`common/review.py`, `backend/app.py`): shows branch diffs and requires human approve/reject
- **Dashboard** (`backend/static/*`): entity browser, hybrid search, recent changes, run review actions
- **MCP read layer** (`mcp/*.mcp.json`): role-specific MCP configs for content and GTM agents
- **Agent outputs** (`scripts/run_content_agent.py`, `scripts/run_gtm_agent.py`): content draft + GTM prospecting output generated from approved graph data

## Free-tier API Safety (Implemented)

- Sequential global LLM calls with process lock: `common/llm.py`
- Throttle + exponential backoff on 429/quota: `common/llm.py`
- Provider fallback chain: **Gemini -> Groq -> golden fallback**: `common/llm.py`, `pipeline/extract.py`
- Extraction caching for unchanged docs: `pipeline/extract.py` (`.cache/extract`)
- Embedding cache + fallback to deterministic mock vectors: `common/embeddings.py`

## Project Layout

- `cluster/` Omnigraph schemas, queries, Cedar policies
- `pipeline/` seed-data ingestion + extraction + mutation synthesis
- `common/` shared OG client, config, LLM, embeddings, HITL review, diff
- `backend/` FastAPI API + static dashboard/HITL UI
- `scripts/` verification, bootstrap, and agent runners
- `mcp/` MCP config snippets for role-isolated access
- `HF_SPACES_DEPLOY.md` hosting instructions for Docker Space

## Local Run (WSL demo environment)

1. Install Omnigraph + Python deps
2. Generate env/tokens:
   - `python3 scripts/gen_env.py`
3. Apply cluster config:
   - `python3 scripts/apply_cluster.py`
4. Start Omnigraph server:
   - `python3 scripts/start_server.py`
5. In another shell, start FastAPI on a free port (default **8001**; do not use 8000 if another project occupies it):
   - `uvicorn backend.app:app --host 127.0.0.1 --port 8001`
6. Open `http://127.0.0.1:8001`

## End-to-End Flow

1. Run ingestion (branch-only):
   - `python3 -m pipeline.run --run-id demo-01 --use-llm`
2. Review run via API/UI:
   - `GET /api/runs`
   - `GET /api/runs/demo-01`
3. Human approves merge:
   - `POST /api/runs/demo-01/approve`
4. Dashboard + API now read approved `main`
5. Run agents:
   - `python3 scripts/run_content_agent.py`
   - `python3 scripts/run_gtm_agent.py`

## MCP Role Configs + Cedar Scope

- Hosted MCP `--base-url`: `https://arnavkanwar-analytos-brain-v3.hf.space/mcp-proxy` (no trailing slash; FastAPI proxies to Omnigraph on `:8080`)
- Local demo still works with `--base-url http://127.0.0.1:8080` (direct Omnigraph)
- `mcp/content-agent.mcp.json` uses `TOKEN_CONTENT_AGENT`
- `mcp/gtm-agent.mcp.json` uses `TOKEN_GTM_AGENT`
- Cedar policies enforce:
  - `content-agent`: `knowledge` allowed; `market` and `internal` denied
  - `gtm-agent`: `knowledge` + `market` allowed; `internal` denied

Verify:

- `python3 scripts/verify_cedar_scope.py`
- `python3 scripts/verify_access.py`

## Hugging Face Spaces (Docker)

- `Dockerfile` + `hf/start.sh` included
- single external port (`7860`) through FastAPI
- startup bootstrap supports ephemeral storage (`gen_env.py` + `apply_cluster.py`)

Full steps: `HF_SPACES_DEPLOY.md`

## Assignment Requirements Coverage Matrix

| Requirement | Status | Concrete verification evidence |
|---|---|---|
| Mandated flow `seed-data -> ingest branch -> diff/HITL -> approve/merge -> dashboard + MCP -> content/GTM agents` | **Done** | `pipeline/run.py` writes `ingest/<run-id>`; HITL endpoints in `backend/app.py`; approve in `common/review.py`; dashboard in `backend/static/*`; MCP configs in `mcp/*.mcp.json`; agent runners in `scripts/run_content_agent.py` + `scripts/run_gtm_agent.py` |
| Free-tier API safety (sequential, throttle, 429 backoff, cache, fallback) | **Done** | `common/llm.py` lock/throttle/backoff/provider fallback; `pipeline/extract.py` cache+golden fallback; `common/embeddings.py` embed cache/fallback |
| HITL web flow + dashboard (entity browser, hybrid search, recent changes) | **Done** | UI implemented in `backend/static/index.html`, `backend/static/app.js`; APIs in `backend/app.py` (`/api/search`, `/api/recent`, `/api/runs`, `/api/runs/{id}/approve`) |
| MCP role configs + Cedar scope proof | **Done** | policy files in `cluster/policies/*.policy.yaml`; role configs in `mcp/*.mcp.json`; `scripts/verify_cedar_scope.py` demonstrates allow/deny matrix |
| Content Agent + GTM Agent outputs | **Done** | `scripts/run_content_agent.py`, `scripts/run_gtm_agent.py` write outputs to `outputs/content-agent-output.md` and `outputs/gtm-agent-output.json` |
| HF Spaces Docker packaging/docs (single-port + bootstrap) | **Done** | `Dockerfile`, `hf/start.sh`, `HF_SPACES_DEPLOY.md` |
| No secrets committed; `.env` gitignored | **Done** | `.gitignore` contains `.env` patterns |
| Local WSL instance retained as persistent demo env | **Done** | Omnigraph on `:8080`; dashboard/HITL on `:8001` (port 8000 left for other projects) |
| Actual HF Spaces deployment execution | **Not yet** | Requires user HF account/repo token and push/deploy action from target Space |

## Current Blockers / Needed User Input

- To complete actual hosted deployment, provide target Hugging Face Space repo/access and permission to push.
- Optional: confirm whether to keep current WSL runtime as-is or harden further (systemd service/supervisor).

