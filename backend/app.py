"""Analytos Brain backend (FastAPI).

Two read layers off `main` live here (dashboard read API), plus the HITL review
surface (list runs, view branch diff, approve->merge / reject->discard). All graph
reads use the `admin` actor (humans see everything, including the internal graph).
The MCP server is the *other* read layer and is Cedar-gated separately.
"""
from __future__ import annotations
import sys, io, contextlib
import random
import time
sys.path.insert(0, "/root/analytos-brain")

from fastapi import FastAPI, HTTPException, Body, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pathlib

from common.og import OG, OGError
from common import review
from common.diff import compute_diff
from pipeline.run import run_ingestion
from scripts import run_content_agent, run_gtm_agent

ROOT = pathlib.Path("/root/analytos-brain")
STATIC = pathlib.Path(__file__).resolve().parent / "static"

app = FastAPI(title="Analytos Brain", version="1.0")
admin = OG("admin")


def _is_concurrent_modification_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "concurrent modification" in text or "table version" in text


def rows(result: dict) -> list[dict]:
    """Strip the 'var.' prefix from stored-query row keys."""
    out = []
    for r in result.get("rows", []):
        out.append({k.split(".", 1)[-1]: v for k, v in r.items()})
    return out


def q(graph, name, params=None, branch="main"):
    return rows(admin.query(graph, name, params=params, branch=branch))


@app.middleware("http")
async def prevent_stale_static_cache(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path in {"/", "/index.html", "/app.js", "/styles.css"}:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ----------------------------------------------------------------- dashboard read
@app.get("/api/health")
def health():
    return admin.healthz()


@app.get("/api/stats")
def stats():
    def n(g, name):
        try:
            return admin.query(g, name, branch="main").get("row_count", 0)
        except OGError:
            return 0
    return {
        "knowledge": {"products": n("knowledge", "list_products"),
                      "features": n("knowledge", "list_features"),
                      "proof_points": n("knowledge", "list_proof_points"),
                      "competitors": n("knowledge", "list_competitors")},
        "market": {"icp_segments": n("market", "list_icp_segments"),
                   "personas": n("market", "list_personas")},
        "internal": {"email_threads": n("internal", "list_email_threads"),
                     "decisions": n("internal", "list_decisions"),
                     "people": n("internal", "list_people")},
    }


@app.get("/api/products")
def products():
    return q("knowledge", "list_products")


@app.get("/api/products/{slug}")
def product(slug: str):
    prod = q("knowledge", "get_product", {"slug": slug})
    if not prod:
        raise HTTPException(404, "product not found")
    return {
        "product": prod[0],
        "features": q("knowledge", "product_features", {"slug": slug}),
        "proof_points": q("knowledge", "product_proof_points", {"slug": slug}),
        "competitors": q("knowledge", "product_competitors", {"slug": slug}),
    }


@app.get("/api/proof_points")
def proof_points():
    return q("knowledge", "list_proof_points")


@app.get("/api/features")
def features():
    return q("knowledge", "list_features")


@app.get("/api/competitors")
def competitors():
    return q("knowledge", "list_competitors")


@app.get("/api/icp")
def icp():
    return q("market", "list_icp_segments")


@app.get("/api/icp/{slug}")
def icp_one(slug: str):
    seg = q("market", "get_icp_segment", {"slug": slug})
    if not seg:
        raise HTTPException(404, "segment not found")
    return {"segment": seg[0], "personas": q("market", "segment_personas", {"slug": slug})}


@app.get("/api/personas")
def personas():
    return q("market", "list_personas")


@app.get("/api/internal/threads")
def threads():
    return q("internal", "list_email_threads")


@app.get("/api/internal/threads/{slug}")
def thread(slug: str):
    t = q("internal", "get_email_thread", {"slug": slug})
    if not t:
        raise HTTPException(404, "thread not found")
    return t[0]


@app.get("/api/internal/decisions")
def decisions():
    return q("internal", "list_decisions")


@app.get("/api/internal/people")
def people():
    return q("internal", "list_people")


# -------------------------------------------------- OG hybrid search (vector+bm25 RRF)
# Stored queries fuse vector ANN (nearest, gemini query-time auto-embed) with bm25 via
# rrf() in one runtime. (graph, stored_query, type, title_field, snippet_field).
HYBRID_TARGETS = [
    ("knowledge", "search_products", "Product", "name", "description"),
    ("knowledge", "search_features", "Feature", "name", "description"),
    ("knowledge", "search_proof_points", "ProofPoint", "statement", "statement"),
    ("market", "search_icp", "ICPSegment", "name", "description"),
    ("market", "search_personas", "Persona", "name", "cares_about"),
]
# lexical fallback if the hybrid query fails (e.g. embedder unreachable)
FALLBACK_TARGETS = [
    ("knowledge", "Product", "name", "description"),
    ("knowledge", "ProofPoint", "statement", "statement"),
    ("market", "ICPSegment", "name", "description"),
    ("internal", "EmailThread", "subject", "summary"),
    ("internal", "Decision", "statement", "statement"),
]


def _bm25_fallback(q, limit):
    results = []
    for graph, typ, title_f, search_f in FALLBACK_TARGETS:
        proj = f"$n.slug, $n.{search_f}" if title_f == search_f else f"$n.slug, $n.{title_f}, $n.{search_f}"
        src = (f"query s($term: String) {{ match {{ $n: {typ} "
               f"match_text($n.{search_f}, $term) }} return {{ {proj} }} "
               f"order {{ bm25($n.{search_f}, $term) }} limit {limit} }}")
        try:
            res = admin.query_adhoc(graph, src, {"term": q}, branch="main")
        except OGError:
            continue
        for r in rows(res):
            results.append({"graph": graph, "type": typ, "slug": r.get("slug"),
                            "title": r.get(title_f) or r.get(search_f) or r.get("slug"),
                            "snippet": r.get(search_f) or ""})
    return results


@app.get("/api/search")
def search(q: str, limit: int = 8):
    if not q or not q.strip():
        return {"query": q, "results": []}
    results, degraded = [], False
    for graph, sq, typ, title_f, snip_f in HYBRID_TARGETS:
        try:
            res = admin.query(graph, sq, params={"q": q}, branch="main")
        except OGError:
            degraded = True
            continue
        for r in rows(res):
            results.append({"graph": graph, "type": typ, "slug": r.get("slug"),
                            "title": r.get(title_f) or r.get(snip_f) or r.get("slug"),
                            "snippet": r.get(snip_f) or ""})
    if not results and degraded:  # embedder unreachable -> lexical BM25 fallback
        return {"query": q, "engine": "omnigraph bm25 (lexical fallback)",
                "results": _bm25_fallback(q, limit)}
    return {"query": q,
            "engine": "omnigraph hybrid: vector ANN (nearest) + bm25, fused with rrf()",
            "results": results}


# ---------------------------------------------------------------- recent changes
@app.get("/api/recent")
def recent(limit: int = 25):
    commits = []
    for g in ["knowledge", "market", "internal"]:
        try:
            for c in admin.commits(g, "main"):
                commits.append({
                    "graph": g,
                    "commit": c.get("graph_commit_id"),
                    "actor": c.get("actor_id"),
                    "created_at": c.get("created_at"),
                    "merged_parent": c.get("merged_parent_commit_id"),
                })
        except OGError:
            continue
    commits.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
    run_branches = []
    for run in review.list_runs():
        run_branches.append({
            "run_id": run.get("run_id"),
            "branch": run.get("branch") or f"ingest/{run.get('run_id')}",
            "status": run.get("status"),
            "actor": run.get("approved_by") or run.get("rejected_by") or "pending-human-review",
            "created_at": run.get("created_at"),
        })
    run_branches.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
    events = [
        {
            "kind": "commit",
            "graph": c.get("graph"),
            "branch": "main",
            "ref": c.get("commit"),
            "actor": c.get("actor"),
            "created_at": c.get("created_at"),
        }
        for c in commits[:limit]
    ] + [
        {
            "kind": "branch",
            "graph": "run",
            "branch": b.get("branch"),
            "ref": b.get("run_id"),
            "actor": b.get("actor"),
            "created_at": b.get("created_at"),
        }
        for b in run_branches[:limit]
    ]
    events.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
    return {"events": events[:limit], "commits": commits[:limit], "branches": run_branches[:limit]}


# ------------------------------------------------------------------- HITL review
@app.get("/api/runs")
def runs():
    return {"runs": review.list_runs()}


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str):
    try:
        return review.load_manifest(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "run not found")


@app.post("/api/runs/{run_id}/approve")
def approve(run_id: str, payload: dict = Body(default={})):
    actor_role = payload.get("actor_role", "admin")
    if actor_role not in {"admin", "reviewer"}:
        raise HTTPException(400, "actor_role must be 'admin' or 'reviewer'")
    merge_actor_role = "admin" if actor_role == "reviewer" else actor_role
    try:
        m = review.approve(run_id, actor_role=merge_actor_role)
        if actor_role != merge_actor_role:
            m["approved_requested_by"] = f"act-{actor_role}"
            review.save_manifest(m)
    except FileNotFoundError:
        raise HTTPException(404, "run not found")
    except OGError as e:
        # Fallback retry for rare write-contention races that survive review-level retries.
        if _is_concurrent_modification_error(e):
            time.sleep(0.2 + random.uniform(0.0, 0.1))
            try:
                m = review.approve(run_id, actor_role=merge_actor_role)
                if actor_role != merge_actor_role:
                    m["approved_requested_by"] = f"act-{actor_role}"
                    review.save_manifest(m)
            except OGError as retry_err:
                # Keep approve idempotent if another request completed while we retried.
                try:
                    m = review.load_manifest(run_id)
                    if m.get("status") == "approved":
                        if actor_role != merge_actor_role and not m.get("approved_requested_by"):
                            m["approved_requested_by"] = f"act-{actor_role}"
                            review.save_manifest(m)
                        return {
                            "ok": True,
                            "status": m["status"],
                            "approved_by": m.get("approved_by"),
                            "approved_requested_by": m.get("approved_requested_by"),
                            "actor_role": actor_role,
                            "executed_as": merge_actor_role,
                            "merge_retried": bool(m.get("merge_retried")),
                            "merge_retry_counts": m.get("merge_retry_counts", {}),
                        }
                except FileNotFoundError:
                    pass
                raise HTTPException(
                    409,
                    f"merge conflict after retry; refresh diff and retry approve: {retry_err}",
                )
        else:
            raise HTTPException(400, f"merge failed: {e}")
    return {
        "ok": True,
        "status": m["status"],
        "approved_by": m.get("approved_by"),
        "approved_requested_by": m.get("approved_requested_by"),
        "actor_role": actor_role,
        "executed_as": merge_actor_role,
        "merge_retried": bool(m.get("merge_retried")),
        "merge_retry_counts": m.get("merge_retry_counts", {}),
    }


@app.post("/api/runs/{run_id}/reject")
def reject(run_id: str, payload: dict = Body(default={})):
    actor_role = payload.get("actor_role", "admin")
    if actor_role not in {"admin", "reviewer"}:
        raise HTTPException(400, "actor_role must be 'admin' or 'reviewer'")
    merge_actor_role = "admin" if actor_role == "reviewer" else actor_role
    try:
        m = review.reject(run_id, actor_role=merge_actor_role)
        if actor_role != merge_actor_role:
            m["rejected_requested_by"] = f"act-{actor_role}"
            review.save_manifest(m)
    except FileNotFoundError:
        raise HTTPException(404, "run not found")
    return {
        "ok": True,
        "status": m["status"],
        "rejected_by": m.get("rejected_by"),
        "rejected_requested_by": m.get("rejected_requested_by"),
        "actor_role": actor_role,
        "executed_as": merge_actor_role,
    }


@app.post("/api/runs/{run_id}/discard")
def discard(run_id: str, payload: dict = Body(default={})):
    return reject(run_id, payload)


@app.get("/api/runs/{run_id}/diff")
def run_diff(run_id: str, branch: str | None = Query(default=None)):
    try:
        m = review.load_manifest(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "run not found")
    source_branch = branch or m.get("branch")
    if not source_branch:
        raise HTTPException(400, "run has no branch metadata")
    out = {}
    for g in m.get("graphs", []):
        try:
            out[g] = compute_diff(admin, g, source_branch, base="main")
        except Exception as e:
            out[g] = {"error": str(e), "graph": g, "branch": source_branch}
    return {"run_id": run_id, "branch": source_branch, "base": "main", "diffs": out}


@app.post("/api/ingest")
def ingest(payload: dict = Body(default={})):
    docs = payload.get("docs")
    run_id = payload.get("run_id")
    use_llm = bool(payload.get("use_llm", False))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            m = run_ingestion(docs=docs, run_id=run_id, use_llm=use_llm, log=lambda *a: print(*a))
        except Exception as e:
            raise HTTPException(400, f"ingestion failed: {e}")
    return {"ok": True, "run_id": m["run_id"], "log": buf.getvalue(), "manifest": m}


@app.get("/api/role-scope")
def role_scope_check():
    checks = [
        ("knowledge", "list_products"),
        ("market", "list_icp_segments"),
        ("internal", "list_email_threads"),
    ]
    roles = ["content-agent", "gtm-agent"]
    matrix = {}
    for role in roles:
        client = OG(role)
        row = {}
        for graph, sq in checks:
            try:
                res = client.query(graph, sq, branch="main")
                row[graph] = {"visible": True, "row_count": res.get("row_count", 0)}
            except OGError:
                row[graph] = {"visible": False, "row_count": 0}
        matrix[role] = row
    return {"branch": "main", "matrix": matrix}


@app.post("/api/agents/content-draft")
def generate_content_draft(payload: dict = Body(default={})):
    topic = (payload.get("topic") or "").strip()
    try:
        run_content_agent.run(topic=topic or None)
    except Exception as e:
        raise HTTPException(400, f"content agent failed: {e}")
    out = ROOT / "outputs" / "content-agent-output.md"
    return {"ok": True, "type": "content-draft", "result": out.read_text() if out.exists() else ""}


@app.post("/api/agents/prospect-brief")
def generate_prospect_brief(payload: dict = Body(default={})):
    product = (payload.get("product") or "").strip()
    try:
        run_gtm_agent.run(product_slug=product or None)
    except Exception as e:
        raise HTTPException(400, f"gtm agent failed: {e}")
    out = ROOT / "outputs" / "gtm-agent-output.json"
    return {"ok": True, "type": "prospect-brief", "result": out.read_text() if out.exists() else "{}"}


# ------------------------------------------------------------------------ static
if STATIC.exists():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")


@app.middleware("http")
async def static_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path or "/"
    if path == "/":
        response.headers["Cache-Control"] = "no-store, max-age=0"
    elif path.endswith(".js") or path.endswith(".css") or path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    return response


@app.exception_handler(OGError)
def og_error_handler(request, exc: OGError):
    return JSONResponse(status_code=exc.status, content={"error": str(exc)})
