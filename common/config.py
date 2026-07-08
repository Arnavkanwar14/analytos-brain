"""Shared config + secrets loading for the Analytos Brain (pipeline, backend, agents)."""
import os, pathlib, functools
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
LOCALHOST_OG_BIND = "127.0.0.1:8080"
LOCALHOST_OG_URL = "http://127.0.0.1:8080"


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




def is_hf_space() -> bool:
    if get("HF_SPACE") == "1":
        return True
    if get("SPACE_ID"):
        return True
    return get("PORT") == "7860"


def _localhost_host(host: str | None) -> bool:
    return (host or "").lower() in {"127.0.0.1", "localhost", "::1"}


def assert_localhost_og_url(url: str) -> str:
    host = urlparse(url).hostname
    if not _localhost_host(host):
        raise RuntimeError(
            f"HF Space requires Omnigraph on localhost only, got {url!r}"
        )
    return url.rstrip("/")


def resolve_omnigraph_base_url() -> str:
    url = get("OMNIGRAPH_BASE_URL", LOCALHOST_OG_URL) or LOCALHOST_OG_URL
    if is_hf_space():
        return assert_localhost_og_url(url)
    return url.rstrip("/")


def resolve_omnigraph_bind() -> str:
    bind = get("OMNIGRAPH_BIND", LOCALHOST_OG_BIND) or LOCALHOST_OG_BIND
    if is_hf_space():
        host = bind.rsplit(":", 1)[0]
        if not _localhost_host(host):
            return LOCALHOST_OG_BIND
    return bind

BASE_URL = resolve_omnigraph_base_url()

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
