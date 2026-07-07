"""Extraction step: unstructured markdown -> typed graph records.

Provider chain (rate-limit disciplined, see common/llm.py): Gemini -> Groq -> golden.
Per-document caching keyed by a hash of the file contents means the idempotent
pipeline does NOT re-call any LLM for unchanged documents. Output shape:
    {"nodes": [{"graph","type","data"}...], "edges": [{"graph","edge","from","to"}...]}
"""
from __future__ import annotations
import json, hashlib, pathlib
from . import golden, ontology
from common import config, llm

PROMPT_VERSION = "v1"
CACHE_DIR = pathlib.Path("/root/analytos-brain/.cache/extract")

SYSTEM = """You are a careful knowledge-graph extractor for Analytos, a company that
builds AI products for discrete manufacturing. Convert the given internal document into
typed graph records for a governed company knowledge graph. Output must be JSON.

Return ONLY a JSON object: {"nodes": [...], "edges": [...]}.

Route every node to exactly one graph:
- knowledge: Product, Feature, ProofPoint, Competitor   (externally shareable product truth)
- market:    ICPSegment, Persona                        (ideal-customer + buyer personas)
- internal:  EmailThread, Person, Decision              (raw email + internal decisions; NEVER external)

Rules:
- Each node: {"graph","type","data":{...}}; data MUST include a stable lowercase-kebab "slug"
  and all required fields. Product/Feature/Competitor/ICPSegment/Persona/Person need "name";
  ProofPoint needs "statement" and boolean "approved_external"; EmailThread needs "subject"
  and boolean "confidential"; Decision needs "statement".
- ProofPoint: capture metrics STRUCTURED, not as blobs: metric, magnitude (number), unit
  (%, hours, days, minutes, USD, count), direction (reduction|increase|absolute|range),
  value_before, value_after, window. Set approved_external=true ONLY when the document
  explicitly approves external use. Set source_doc to the document name, and source_thread
  to the related email thread slug when known (traceability).
- Feature slug = "<product-slug>-<kebab-name>". ProofPoint slug = "<product>-<metric-keywords>-<direction>".
- Email docs: create the EmailThread (confidential=true, include a faithful body), a Person per
  participant, and a Decision per explicit instruction/decision. Keep client names and sharper
  internal-only numbers on the internal graph only.
- Edges: {"graph","edge","from","to"} using slugs. Allowed: knowledge[HasFeature,ProvenBy,
  FeatureProvenBy,Displaces]; market[HasPersona]; internal[AuthoredBy,DiscussedIn,DecidedBy].
"""


def _example() -> str:
    return json.dumps(golden.golden_for("stockly-product-overview.md"), separators=(",", ":"))


def _cache_key(doc_name: str, text: str) -> str:
    h = hashlib.sha256(f"{PROMPT_VERSION}\x00{doc_name}\x00{text}".encode()).hexdigest()[:16]
    return h


def _cache_path(doc_name: str, text: str) -> pathlib.Path:
    return CACHE_DIR / f"{doc_name}.{_cache_key(doc_name, text)}.json"


def _tag(data: dict, doc_name: str) -> dict:
    for n in data.get("nodes", []):
        n.setdefault("graph", ontology.graph_of_node(n.get("type")))
        n.setdefault("data", {}).setdefault("source_doc", doc_name)
    for e in data.get("edges", []):
        e.setdefault("graph", ontology.graph_of_edge(e.get("edge")))
    return data


def extract_with_llm(doc_name: str, text: str, log=print) -> tuple[dict, str]:
    prompt = (f"Example (for 'stockly-product-overview.md') ->\n{_example()}\n\n"
              f"Now extract document '{doc_name}'. Return ONLY the JSON object.\n---\n{text}\n---")
    data, provider = llm.complete_json(SYSTEM, prompt, temperature=0.0, log=log)
    data = _tag(data, doc_name)
    if not data.get("nodes"):
        raise ValueError("LLM returned no nodes")
    return data, provider


def extract_document(doc_name: str, text: str, use_llm: bool, log=print) -> tuple[dict, str]:
    """Returns (extraction, method). method is one of:
    'golden', 'cache:<provider>', '<provider>', or 'golden(fallback)'."""
    if not use_llm:
        return golden.golden_for(doc_name), "golden"

    # 1) cache hit for unchanged doc -> no LLM call
    cp = _cache_path(doc_name, text)
    if cp.exists():
        try:
            cached = json.loads(cp.read_text())
            return cached["extraction"], f"cache:{cached.get('provider', 'llm')}"
        except Exception:
            pass

    # 2) live LLM via provider chain (Gemini -> Groq)
    try:
        data, provider = extract_with_llm(doc_name, text, log=log)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({"provider": provider, "doc": doc_name, "extraction": data}, indent=2))
        return data, provider
    except Exception as e:  # noqa: BLE001 — includes NoProviderAvailable / quota exhaustion
        log(f"  [warn] LLM extraction failed for {doc_name} ({type(e).__name__}: {str(e)[:120]}); "
            f"falling back to golden")
        return golden.golden_for(doc_name), "golden(fallback)"
