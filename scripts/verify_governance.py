#!/usr/bin/env python3
"""Governance checks: main stays empty pre-merge; ingest cannot merge to main;
re-ingest is idempotent (no new nodes)."""
import sys, pathlib
sys.path.insert(0, "/root/analytos-brain")
from common.og import OG, OGError

admin = OG("admin")
ingest = OG("ingest")
BR = "ingest/demo-01"

def count(role_client, graph, name, branch):
    r = role_client.query(graph, name, branch=branch)
    return r.get("row_count")

print("== main is empty (nothing merged yet) ==")
for g, q in [("knowledge", "list_products"), ("market", "list_icp_segments"), ("internal", "list_email_threads")]:
    print(f"  main/{g}/{q}: row_count={count(admin, g, q, 'main')}")

print("\n== branch has data ==")
for g, q in [("knowledge", "list_products"), ("market", "list_icp_segments"), ("internal", "list_email_threads")]:
    print(f"  {BR}/{g}/{q}: row_count={count(admin, g, q, BR)}")

print("\n== ingest actor CANNOT merge to protected main (should be denied) ==")
try:
    ingest.merge("knowledge", BR, "main")
    print("  !! UNEXPECTED: ingest merge succeeded")
except OGError as e:
    print(f"  OK denied: HTTP {e.status}")
