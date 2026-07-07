"""Document-side embeddings for hybrid retrieval.

Produces 768-dim vectors in the SAME space the cluster's query-time embedder uses
(gemini-embedding-001 @ outputDimensionality=768), so stored doc vectors and the
auto-embedded query vector are comparable under cosine. Disciplined like the LLM
layer: sequential, throttled, backoff on 429, cached per (model, dim, text) hash.
Falls back to a deterministic offline `mock` vector so ingestion never hard-fails
(matches Omnigraph's own `mock` provider contract: correct dim, unit L2 norm).
"""
from __future__ import annotations
import time, json, hashlib, math, struct, pathlib, urllib.request, threading

from . import config

MODEL = "gemini-embedding-001"
DIM = 768
CACHE_DIR = pathlib.Path("/root/analytos-brain/.cache/embed")
MIN_INTERVAL = float(config.get("LLM_MIN_INTERVAL_S", "5") or 5) / 5.0  # embeds are cheaper
MAX_RETRIES = int(config.get("LLM_MAX_RETRIES", "4") or 4)

_lock = threading.Lock()
_last = 0.0
_gemini_disabled = False

# per-node-type embedding source field (mirrors the .pg @embed annotations)
SOURCE_FIELD = {
    "Product": "description", "Feature": "description", "ProofPoint": "statement",
    "Competitor": "note", "ICPSegment": "description", "Persona": "cares_about",
}


def _throttle():
    global _last
    wait = MIN_INTERVAL - (time.time() - _last)
    if wait > 0:
        time.sleep(wait)
    _last = time.time()


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _mock_vector(text: str) -> list[float]:
    """Deterministic unit vector seeded from the text hash (no key needed)."""
    seed = hashlib.sha256(text.encode()).digest()
    out = []
    i = 0
    while len(out) < DIM:
        h = hashlib.sha256(seed + struct.pack("<I", i)).digest()
        for j in range(0, len(h), 4):
            if len(out) >= DIM:
                break
            out.append((struct.unpack("<I", h[j:j + 4])[0] / 2**32) - 0.5)
        i += 1
    return _l2(out)


def _gemini_embed(text: str) -> list[float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:embedContent"
    body = json.dumps({
        "model": f"models/{MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_DOCUMENT",
        "outputDimensionality": DIM,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "x-goog-api-key": config.GEMINI_API_KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return _l2(d["embedding"]["values"])


def _cache_path(text: str) -> pathlib.Path:
    key = hashlib.sha256(f"{MODEL}\x00{DIM}\x00{text}".encode()).hexdigest()[:20]
    return CACHE_DIR / f"{key}.json"


def embed_text(text: str, log=print) -> tuple[list[float], str]:
    """Return (vector, provider). provider in {gemini, cache:gemini, mock}."""
    global _gemini_disabled
    text = (text or "").strip()
    if not text:
        return _mock_vector("<empty>"), "mock"
    cp = _cache_path(text)
    if cp.exists():
        try:
            c = json.loads(cp.read_text())
            return c["vector"], f"cache:{c.get('provider', 'gemini')}"
        except Exception:
            pass
    with _lock:
        if config.GEMINI_API_KEY and not _gemini_disabled:
            for attempt in range(MAX_RETRIES):
                _throttle()
                try:
                    v = _gemini_embed(text)
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    cp.write_text(json.dumps({"provider": "gemini", "model": MODEL, "vector": v}))
                    return v, "gemini"
                except Exception as e:  # noqa: BLE001
                    s = str(e).lower()
                    if ("429" in s or "quota" in s or "resource" in s) and attempt < MAX_RETRIES - 1:
                        time.sleep(MIN_INTERVAL * (2 ** attempt))
                        continue
                    log(f"[embed] gemini failed ({type(e).__name__}: {str(e)[:100]}); using mock")
                    _gemini_disabled = True
                    break
    return _mock_vector(text), "mock"


def embed_node(node: dict, log=print) -> str | None:
    """Attach node.data['embedding'] from the type's source field. Returns provider used."""
    typ = node.get("type")
    field = SOURCE_FIELD.get(typ)
    if not field:
        return None
    text = (node.get("data", {}) or {}).get(field)
    if not text:
        return None
    vec, provider = embed_text(text, log=log)
    node["data"]["embedding"] = vec
    return provider
