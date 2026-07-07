#!/usr/bin/env python3
"""Approve demo-01 (human merge -> main) and verify main is populated + attributed."""
import sys
sys.path.insert(0, "/root/analytos-brain")
from common import review
from common.og import OG

print("== approve run demo-01 (merge as act-admin) ==")
m = review.approve("demo-01", actor_role="admin")
print("  status:", m["status"], "approved_by:", m.get("approved_by"))

admin = OG("admin")
print("\n== main now populated (post-merge) ==")
for g, q in [("knowledge", "list_products"), ("knowledge", "list_proof_points"),
             ("market", "list_icp_segments"), ("market", "list_personas"),
             ("internal", "list_email_threads"), ("internal", "list_decisions")]:
    print(f"  main/{g}/{q}: row_count={admin.query(g, q, branch='main').get('row_count')}")

print("\n== merge commit attribution on main (head commit actor) ==")
for g in ["knowledge", "market", "internal"]:
    commits = admin.commits(g, "main")
    head = commits[-1] if commits else {}
    print(f"  {g}: head actor_id={head.get('actor_id')} commit={head.get('graph_commit_id')}")
