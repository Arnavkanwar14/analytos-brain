#!/usr/bin/env python3
"""Approve (merge to main) or reject a pending ingestion run as the admin/human actor.
Usage: approve_run.py <run-id> [reject]"""
import sys
sys.path.insert(0, "/root/analytos-brain")
from common import review

run_id = sys.argv[1]
action = sys.argv[2] if len(sys.argv) > 2 else "approve"
m = (review.reject if action == "reject" else review.approve)(run_id, actor_role="admin")
print(f"{action} {run_id}: status={m['status']} "
      f"by={m.get('approved_by') or m.get('rejected_by')}")
