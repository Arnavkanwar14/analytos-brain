#!/usr/bin/env python3
"""Discover load/export/branch/commit HTTP body shapes on a throwaway branch.
Creates ingest/probe on knowledge, loads one node, inspects, then deletes the branch."""
import json, urllib.request, urllib.error, pathlib

ENV = pathlib.Path("/root/analytos-brain/.env")
E = {}
for line in ENV.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        E[k.strip()] = v.strip()
BASE = E["OMNIGRAPH_BASE_URL"]

def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return -1, str(e)

INGEST = E["TOKEN_INGEST"]
ADMIN = E["TOKEN_ADMIN"]
BR = "ingest/probe"
ndjson = '{"type":"Product","data":{"slug":"__probe","name":"Probe","approved_external":false}}'

print("== LOAD (ingest) create branch from main ==")
for shape in (
    {"data": ndjson, "mode": "merge", "from": "main", "branch": BR},
    {"data": ndjson, "mode": "merge", "from_branch": "main", "branch": BR},
    {"ndjson": ndjson, "mode": "merge", "from": "main", "branch": BR},
):
    st, bd = call("POST", "/graphs/knowledge/load", INGEST, shape)
    print(f"  keys={list(shape)} -> {st}  {bd[:220]}")
    if st == 200:
        break

print("\n== BRANCHES list (admin) ==")
print(call("GET", "/graphs/knowledge/branches", ADMIN))

print("\n== COMMITS on branch (admin) ==")
print(call("GET", f"/graphs/knowledge/commits?branch={urllib.parse.quote(BR, safe='')}", ADMIN))

print("\n== EXPORT branch (admin) ==")
for shape in ({"branch": BR}, {"branch": BR, "format": "jsonl"}):
    st, bd = call("POST", "/graphs/knowledge/export", ADMIN, shape)
    print(f"  keys={list(shape)} -> {st}  {bd[:220]}")
    if st == 200:
        break

print("\n== SNAPSHOT branch (admin) ==")
print(call("GET", f"/graphs/knowledge/snapshot?branch={urllib.parse.quote(BR, safe='')}", ADMIN)[0:2])

print("\n== cleanup: delete probe branch (admin) ==")
print(call("DELETE", f"/graphs/knowledge/branches/{urllib.parse.quote(BR, safe='')}", ADMIN))
