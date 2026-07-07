"""Ingestion run: seed docs -> extract -> typed mutations -> ONE ingest branch per
graph (never main) -> diff. A human approves/merges later via the review UI.

Usage:
  python -m pipeline.run                      # all seed docs, golden extraction
  python -m pipeline.run --use-llm            # use Gemini if GEMINI_API_KEY set
  python -m pipeline.run --docs seed-data/x.md --run-id demo-01
"""
from __future__ import annotations
import argparse, datetime, glob, json, os, pathlib, sys

from common import config, embeddings
from common.og import OG
from common.diff import compute_diff
from . import extract, mutations

ROOT = pathlib.Path("/root/analytos-brain")
SEED = ROOT / "seed-data"
RUNS = ROOT / "runs"


def new_run_id() -> str:
    return "run-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def run_ingestion(docs=None, run_id=None, use_llm=False, log=print) -> dict:
    """Core ingestion: extract -> typed mutations -> ingest branch (never main) -> diff.
    Returns the run manifest dict. Callable from CLI or the backend."""
    docs = docs or sorted(glob.glob(str(SEED / "*.md")))
    if not docs:
        raise RuntimeError("no seed docs found")
    run_id = run_id or new_run_id()
    branch = f"ingest/{run_id}"
    RUNS.mkdir(exist_ok=True)

    log(f"== ingestion run {run_id} ==")
    log(f"docs: {[os.path.basename(d) for d in docs]}")

    # 1) extract every doc and aggregate
    agg = {"nodes": [], "edges": []}
    methods = {}
    for d in docs:
        name = os.path.basename(d)
        # allow passing bare filenames that live in seed-data/
        path = pathlib.Path(d)
        if not path.exists():
            path = SEED / name
        text = path.read_text(encoding="utf-8")
        ext, method = extract.extract_document(name, text, use_llm=use_llm)
        methods[name] = method
        agg["nodes"] += ext.get("nodes", [])
        agg["edges"] += ext.get("edges", [])
        log(f"  extracted {name}: {len(ext.get('nodes', []))} nodes, "
            f"{len(ext.get('edges', []))} edges  [{method}]")

    grouped = mutations.by_graph(mutations.normalize(agg))

    # 1b) attach hybrid-retrieval vectors (gemini @768, cached; mock fallback). Sequential.
    embed_providers = {}
    n_embedded = 0
    for g in config.GRAPHS:
        for node in grouped[g]["nodes"].values():
            p = embeddings.embed_node(node, log=log)
            if p:
                embed_providers[p] = embed_providers.get(p, 0) + 1
                n_embedded += 1
    if n_embedded:
        log(f"  embedded {n_embedded} nodes for hybrid search: {embed_providers}")

    # 2) load each graph's payload onto the ingest branch (forked from main). NEVER main.
    ingest = OG("ingest")
    admin = OG("admin")
    touched = []
    for g in config.GRAPHS:
        bundle = grouped[g]
        if not bundle["nodes"] and not bundle["edges"]:
            continue
        ndjson = mutations.to_ndjson(bundle)
        exists = branch in admin.branches(g)
        res = ingest.load(g, ndjson, mode="merge", branch=branch,
                          from_branch=None if exists else "main")
        loaded = sum(t.get("rows_loaded", 0) for t in res.get("tables", []))
        log(f"  [{g}] loaded {loaded} rows onto {branch} (actor={res.get('actor_id')})")
        touched.append(g)

    # 3) diff each touched graph vs main (as admin, who can read both)
    diffs = {}
    for g in touched:
        diffs[g] = compute_diff(admin, g, branch, base="main")
        c = diffs[g]["counts"]
        log(f"  [{g}] diff vs main: +{c['added_nodes']} nodes, "
            f"~{c['changed_nodes']} changed, +{c['added_edges']} edges")

    manifest = {
        "run_id": run_id, "branch": branch,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "docs": [os.path.basename(d) for d in docs],
        "extraction_methods": methods,
        "embedding_providers": embed_providers,
        "graphs": touched, "status": "pending",
        "diffs": diffs,
    }
    (RUNS / f"{run_id}.json").write_text(json.dumps(manifest, indent=2))
    log(f"\nwrote run manifest: runs/{run_id}.json  (status=pending, awaiting human review)")
    log("branches created (NOT on main): " + ", ".join(f"{g}:{branch}" for g in touched))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", nargs="*", help="doc paths (default: all seed-data/*.md)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--use-llm", action="store_true", help="use Gemini extraction if key present")
    args = ap.parse_args()
    run_ingestion(docs=args.docs, run_id=args.run_id, use_llm=args.use_llm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
