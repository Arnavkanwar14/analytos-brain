#!/usr/bin/env python3
"""Generate stable bearer tokens + .env for the Analytos Brain server and clients.
Idempotent: if .env already has tokens, it is left untouched so tokens stay stable."""
import os, secrets, json, pathlib

ROOT = pathlib.Path("/root/analytos-brain")
ENV = ROOT / ".env"

ACTORS = {
    "TOKEN_ADMIN": "act-admin",
    "TOKEN_REVIEWER": "act-reviewer",
    "TOKEN_CONTENT_AGENT": "act-content-agent",
    "TOKEN_GTM_AGENT": "act-gtm-agent",
    "TOKEN_INGEST": "act-ingest",
}

def load_existing():
    vals = {}
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals


def pick(key: str, existing: dict, default: str = "") -> str:
    """Prefer real process env (HF Space secrets), then .env file, then default."""
    return os.environ.get(key) or existing.get(key) or default


def main():
    existing = load_existing()
    tokens = {}
    for var in ACTORS:
        tokens[var] = pick(var, existing) or secrets.token_urlsafe(24)

    # actor_id -> token  (what the server consumes)
    bearer_map = {actor: tokens[var] for var, actor in ACTORS.items()}

    lines = [
        "# Analytos Brain — secrets & runtime config. GIT-IGNORED. Do not commit.",
        "OMNIGRAPH_BASE_URL=http://127.0.0.1:8080",
        "OMNIGRAPH_BIND=127.0.0.1:8080",
        f"GEMINI_API_KEY={pick('GEMINI_API_KEY', existing)}",
        f"GROQ_API_KEY={pick('GROQ_API_KEY', existing)}",
        f"GEMINI_MODEL={pick('GEMINI_MODEL', existing, 'gemini-2.0-flash')}",
        "",
        "# Per-actor bearer tokens (client side)",
    ]
    for var in ACTORS:
        lines.append(f"{var}={tokens[var]}")
    lines += [
        "",
        "# Combined actor->token map consumed by omnigraph-server",
        "OMNIGRAPH_SERVER_BEARER_TOKENS_JSON=" + json.dumps(bearer_map, separators=(",", ":")),
        "",
    ]
    ENV.write_text("\n".join(lines))
    os.chmod(ENV, 0o600)
    print(f"wrote {ENV} (mode 600)")
    print("actors:", ", ".join(ACTORS.values()))
    print("GEMINI_API_KEY set:", bool(pick("GEMINI_API_KEY", existing)))
    print("GROQ_API_KEY set:", bool(pick("GROQ_API_KEY", existing)))

if __name__ == "__main__":
    main()
