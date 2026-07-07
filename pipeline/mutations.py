"""Turn an extraction dict into per-graph NDJSON load payloads.

Idempotency: nodes carry stable @key slugs and are loaded with mode=merge (upsert),
so re-ingesting the same document updates rather than duplicates. Within a run we
also dedupe identical (type, slug) nodes (e.g. a Person appearing in two threads)."""
from __future__ import annotations
import json, re
from . import ontology


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def _validate_node(rec: dict) -> list[str]:
    problems = []
    g, t, data = rec.get("graph"), rec.get("type"), rec.get("data", {})
    spec = ontology.NODES.get(g, {}).get(t)
    if spec is None:
        return [f"unknown node type {t!r} for graph {g!r}"]
    for f in spec["required"]:
        if data.get(f) in (None, ""):
            problems.append(f"{t}/{data.get('slug','?')}: missing required '{f}'")
    return problems


def normalize(extraction: dict) -> dict:
    """Ensure required defaults + stable slugs; return {'nodes':[...], 'edges':[...]}."""
    nodes, edges = [], []
    for rec in extraction.get("nodes", []):
        t, data = rec.get("type"), dict(rec.get("data", {}))
        g = rec.get("graph") or ontology.graph_of_node(t)
        if not data.get("slug") and data.get("name"):
            data["slug"] = slugify(data["name"])
        # sensible defaults for non-nullable gate fields
        if t == "ProofPoint" and "approved_external" not in data:
            data["approved_external"] = False
        if t == "EmailThread" and "confidential" not in data:
            data["confidential"] = True
        nodes.append({"graph": g, "type": t, "data": data})
    for rec in extraction.get("edges", []):
        e = rec.get("edge")
        edges.append({"graph": rec.get("graph") or ontology.graph_of_edge(e),
                      "edge": e, "from": rec["from"], "to": rec["to"]})
    return {"nodes": nodes, "edges": edges}


def by_graph(records: dict) -> dict:
    """Group nodes+edges per graph, deduped, and validated."""
    out = {g: {"nodes": {}, "edges": []} for g in ontology.NODES}
    problems = []
    for n in records["nodes"]:
        problems += _validate_node(n)
        g = n["graph"]
        out[g]["nodes"][(n["type"], n["data"]["slug"])] = n
    seen_edges = set()
    for e in records["edges"]:
        key = (e["graph"], e["edge"], e["from"], e["to"])
        if key in seen_edges:
            continue
        seen_edges.add(key)
        out[e["graph"]]["edges"].append(e)
    if problems:
        raise ValueError("extraction validation failed:\n  " + "\n  ".join(problems))
    return out


def to_ndjson(graph_bundle: dict) -> str:
    """Serialize one graph's nodes+edges to Omnigraph load NDJSON."""
    lines = []
    for (_type, _slug), n in graph_bundle["nodes"].items():
        lines.append(json.dumps({"type": n["type"], "data": n["data"]}, separators=(",", ":")))
    for e in graph_bundle["edges"]:
        lines.append(json.dumps({"edge": e["edge"], "from": e["from"], "to": e["to"], "data": {}},
                                separators=(",", ":")))
    return "\n".join(lines)
