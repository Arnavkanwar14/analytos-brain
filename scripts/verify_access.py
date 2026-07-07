#!/usr/bin/env python3
"""Prove the Cedar access matrix over HTTP + discover request-body shapes.
Uses only the stdlib. Reads tokens from /root/analytos-brain/.env."""
import json, urllib.request, urllib.error, pathlib

ENV = pathlib.Path("/root/analytos-brain/.env")

def env():
    d = {}
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d

E = env()
BASE = E["OMNIGRAPH_BASE_URL"]
TOK = {
    "admin": E["TOKEN_ADMIN"],
    "content-agent": E["TOKEN_CONTENT_AGENT"],
    "gtm-agent": E["TOKEN_GTM_AGENT"],
    "ingest": E["TOKEN_INGEST"],
}

def call(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode()[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return -1, str(e)

print("== healthz ==")
print(call("GET", "/healthz"))

print("\n== GET /graphs (admin) ==")
print(call("GET", "/graphs", TOK["admin"]))

# Discover invoke-body shape with admin on a no-arg stored query
print("\n== discover invoke body shape (admin, knowledge/list_products) ==")
for shape in ({"params": {}}, {}, {"params": {}, "branch": "main"}):
    st, bd = call("POST", "/graphs/knowledge/queries/list_products", TOK["admin"], shape)
    print(f"  shape={shape} -> {st}  {bd[:120]}")

print("\n== ACCESS MATRIX (stored-query invocation; 200=allowed, 403/404=denied) ==")
graphs = {
    "knowledge": "list_products",
    "market": "list_icp_segments",
    "internal": "list_email_threads",
}
actors = ["admin", "content-agent", "gtm-agent"]
print(f"{'actor':<15}" + "".join(f"{g:<12}" for g in graphs))
for a in actors:
    row = f"{a:<15}"
    for g, q in graphs.items():
        st, _ = call("POST", f"/graphs/{g}/queries/{q}", TOK[a], {"params": {}})
        row += f"{st:<12}"
    print(row)
