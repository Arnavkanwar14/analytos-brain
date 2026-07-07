"""Compute a node/edge diff of a branch vs a base branch (default main), using an
admin OG client that can read both. Powers the HITL review surface."""
from __future__ import annotations

VOLATILE = {"id"}


def _node_key(rec):
    d = rec.get("data", {})
    return (rec.get("type"), d.get("slug") or d.get("id"))


def _node_data(rec):
    return {k: v for k, v in rec.get("data", {}).items() if k not in VOLATILE}


def _edge_key(rec):
    d = rec.get("data", {})
    frm = rec.get("from") or d.get("from") or d.get("src")
    to = rec.get("to") or d.get("to") or d.get("dst")
    return (rec.get("edge") or rec.get("type"), frm, to)


def _split(records):
    nodes, edges = {}, {}
    for rec in records:
        if "edge" in rec or (rec.get("type", "").startswith("edge")):
            edges[_edge_key(rec)] = rec
        else:
            nodes[_node_key(rec)] = rec
    return nodes, edges


def compute_diff(og, graph, branch, base="main"):
    try:
        base_recs = og.export(graph, base)
    except Exception:
        base_recs = []
    branch_recs = og.export(graph, branch)
    bn, be = _split(base_recs)
    tn, te = _split(branch_recs)

    added_nodes, changed_nodes = [], []
    for k, rec in tn.items():
        if k not in bn:
            added_nodes.append({"type": rec.get("type"), "slug": k[1], "data": _node_data(rec)})
        elif _node_data(rec) != _node_data(bn[k]):
            changed_nodes.append({"type": rec.get("type"), "slug": k[1],
                                  "before": _node_data(bn[k]), "after": _node_data(rec)})
    added_edges = [{"edge": k[0], "from": k[1], "to": k[2]} for k in te if k not in be]

    return {
        "graph": graph, "branch": branch, "base": base,
        "added_nodes": sorted(added_nodes, key=lambda x: (x["type"], x["slug"] or "")),
        "changed_nodes": changed_nodes,
        "added_edges": added_edges,
        "counts": {"added_nodes": len(added_nodes), "changed_nodes": len(changed_nodes),
                   "added_edges": len(added_edges), "base_nodes": len(bn), "branch_nodes": len(tn)},
    }
