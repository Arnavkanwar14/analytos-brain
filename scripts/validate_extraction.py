#!/usr/bin/env python3
"""Validate real LLM extraction (provider chain) against golden expectations, per doc.
Extraction only (no branch load) so it does not pollute graphs. Results are cached."""
import sys, glob, os, pathlib, collections
sys.path.insert(0, "/root/analytos-brain")
from pipeline import extract, mutations, golden

SEED = "/root/analytos-brain/seed-data"


def counts_by_type(ext):
    c = collections.Counter()
    for n in ext.get("nodes", []):
        c[n.get("type")] += 1
    e = collections.Counter()
    for x in ext.get("edges", []):
        e[x.get("edge")] += 1
    return c, e


for doc in sorted(glob.glob(f"{SEED}/*.md")):
    name = os.path.basename(doc)
    text = pathlib.Path(doc).read_text(encoding="utf-8")
    ext, method = extract.extract_document(name, text, use_llm=True)
    gc, ge = counts_by_type(golden.golden_for(name))
    lc, le = counts_by_type(ext)
    print(f"\n=== {name}  [{method}] ===")
    print(f"  nodes: llm={sum(lc.values())} golden={sum(gc.values())}  by-type(llm)={dict(lc)}")
    print(f"  edges: llm={sum(le.values())} golden={sum(ge.values())}  by-type(llm)={dict(le)}")
    # validate typed shape (required fields present, known types/edges)
    try:
        mutations.by_graph(mutations.normalize(ext))
        print("  validation: OK (typed entities/edges conform to schema)")
    except Exception as ex:
        print(f"  validation: FAILED -> {str(ex)[:300]}")
