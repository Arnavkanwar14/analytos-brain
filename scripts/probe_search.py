#!/usr/bin/env python3
"""Discover which OG search paths work on the current schema (no embeddings yet)."""
import sys
sys.path.insert(0, "/root/analytos-brain")
from common.og import OG, OGError

admin = OG("admin")

def try_q(label, graph, source, params=None):
    try:
        r = admin.query_adhoc(graph, source, params or {}, branch="main")
        print(f"  [OK] {label}: row_count={r.get('row_count')} cols={r.get('columns')}")
    except OGError as e:
        print(f"  [ERR {e.status}] {label}: {e.body[:160]}")
    except Exception as e:
        print(f"  [EXC] {label}: {e}")

print("== ad-hoc /query shape ==")
try_q("plain list", "knowledge", "query q() { match { $p: Product } return { $p.slug, $p.name } limit 5 }")

print("\n== contains filter ==")
try_q("contains", "knowledge",
      "query q($term: String) { match { $p: Product $p.description contains $term } return { $p.slug } limit 5 }",
      {"term": "kanban"})

print("\n== match_text in match block ==")
try_q("match_text", "knowledge",
      "query q($term: String) { match { $p: Product match_text($p.description, $term) } return { $p.slug } limit 5 }",
      {"term": "kanban"})

print("\n== search() in match block ==")
try_q("search", "knowledge",
      "query q($term: String) { match { $p: Product search($p.description, $term) } return { $p.slug } limit 5 }",
      {"term": "kanban"})

print("\n== bm25 in order ==")
try_q("bm25 order", "knowledge",
      "query q($term: String) { match { $p: Product } return { $p.slug } order { bm25($p.description, $term) } limit 5 }",
      {"term": "kanban"})

print("\n== fuzzy in match block ==")
try_q("fuzzy", "knowledge",
      "query q($term: String) { match { $p: Product fuzzy($p.name, $term) } return { $p.slug } limit 5 }",
      {"term": "stockly"})
