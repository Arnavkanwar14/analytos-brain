# Hugging Face Spaces (Docker) Deploy

This project is packaged for **HF Spaces Docker** with single-port routing:

- `omnigraph-server` runs internally on `127.0.0.1:8080`
- FastAPI (`backend.app`) runs on external `0.0.0.0:${PORT:-7860}`
- Static dashboard + HITL UI is served by FastAPI at `/`

## 1) Create Space

1. Create a new Space with **Docker** SDK.
2. Push this repository contents.

## 2) Set Space Secrets

- `GEMINI_API_KEY` (optional but recommended; without it, extraction/agents fallback to Groq/golden)
- `GROQ_API_KEY` (optional fallback tier)
- `PORT` (optional; default `7860`)

No `.env` is committed. `hf/start.sh` creates one at startup via `scripts/gen_env.py`.

## 3) Runtime Bootstrap

Container entrypoint does:

1. `python3 scripts/gen_env.py` (stable actor tokens + server bearer map)
2. `python3 scripts/apply_cluster.py` (validate/import/refresh/apply)
3. start `omnigraph-server`
4. start `uvicorn backend.app:app --port ${PORT:-7860}`

This supports Spaces ephemeral storage by rebuilding local runtime state on boot.

## 4) Validate Deployed App

- `/api/health` returns 200
- `/api/stats` returns non-empty counts after ingest+approve
- `/` renders dashboard + HITL
- `/api/search?q=stock` returns hybrid results (or lexical fallback if embedder unavailable)

## 5) Hosted MCP (Omnigraph proxy)

Omnigraph stays on `127.0.0.1:8080` inside the container. FastAPI exposes a dumb authenticated proxy:

- Base URL: `https://arnavkanwar-analytos-brain-v3.hf.space/mcp-proxy` (no trailing slash)
- Client paths: `{base}/{omnigraph-path}` e.g. `/mcp-proxy/healthz` — avoid `//` by not doubling slashes
- MCP configs: `mcp/content-agent.mcp.json`, `mcp/gtm-agent.mcp.json` use that `--base-url`
- Tokens: `${TOKEN_CONTENT_AGENT}` / `${TOKEN_GTM_AGENT}` (Space secrets); Authorization forwarded verbatim; Cedar remains the gate

