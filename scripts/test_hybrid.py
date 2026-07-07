#!/usr/bin/env python3
"""Prove hybrid retrieval: invoke the stored vector+bm25+rrf queries over the server."""
import sys
sys.path.insert(0, "/root/analytos-brain")
from common.og import OG, OGError

admin = OG("admin")
print("health:", admin.healthz())

tests = [
    ("knowledge", "search_products", "cut excess stock and free up working capital"),
    ("knowledge", "search_proof_points", "faster inventory counts fewer stockouts"),
    ("market", "search_icp", "mid-market ERP manufacturers ready to buy"),
]
for graph, name, q in tests:
    print(f"\n== {graph}.{name}  q='{q}' ==")
    try:
        res = admin.query(graph, name, params={"q": q}, branch="main")
        for i, r in enumerate(res.get("rows", []), 1):
            r = {k.split(".", 1)[-1]: v for k, v in r.items()}
            title = r.get("name") or r.get("statement") or r.get("slug")
            print(f"   #{i} rrf-ranked  {r.get('slug')}  {str(title)[:70]}")
    except OGError as e:
        print("   FAILED:", str(e)[:300])
