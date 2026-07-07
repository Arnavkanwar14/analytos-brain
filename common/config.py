"""Shared config + secrets loading for the Analytos Brain (pipeline, backend, agents)."""
import os, pathlib, functools

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


@functools.lru_cache(maxsize=1)
def env() -> dict:
    d = dict(os.environ)
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d.setdefault(k.strip(), v.strip())  # real env wins over .env
    return d


def get(key: str, default: str | None = None) -> str | None:
    return env().get(key, default)


BASE_URL = get("OMNIGRAPH_BASE_URL", "http://127.0.0.1:8080")

# actor role -> bearer-token env var
TOKENS = {
    "admin": "TOKEN_ADMIN",
    "reviewer": "TOKEN_REVIEWER",
    "content-agent": "TOKEN_CONTENT_AGENT",
    "gtm-agent": "TOKEN_GTM_AGENT",
    "ingest": "TOKEN_INGEST",
}


def token(role: str) -> str:
    var = TOKENS[role]
    tok = get(var)
    if not tok:
        raise RuntimeError(f"missing token for role={role} (env {var}); run scripts/gen_env.py")
    return tok


# graph -> node/edge routing (used by pipeline)
GRAPH_OF_NODE = {
    "Product": "knowledge", "Feature": "knowledge", "ProofPoint": "knowledge", "Competitor": "knowledge",
    "ICPSegment": "market", "Persona": "market",
    "EmailThread": "internal", "Person": "internal", "Decision": "internal",
}
GRAPH_OF_EDGE = {
    "HasFeature": "knowledge", "ProvenBy": "knowledge", "FeatureProvenBy": "knowledge", "Displaces": "knowledge",
    "HasPersona": "market",
    "AuthoredBy": "internal", "DiscussedIn": "internal", "DecidedBy": "internal",
}
GRAPHS = ["knowledge", "market", "internal"]
GEMINI_API_KEY = get("GEMINI_API_KEY")
GEMINI_MODEL = get("GEMINI_MODEL", "gemini-2.0-flash")
