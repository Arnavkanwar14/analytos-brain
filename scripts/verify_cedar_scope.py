#!/usr/bin/env python3
"""Proof of Cedar role scope: content-agent and gtm-agent visibility matrix."""
from __future__ import annotations
import sys

sys.path.insert(0, "/root/analytos-brain")
from common.og import OG, OGError


CHECKS = [
    ("knowledge", "list_products"),
    ("market", "list_icp_segments"),
    ("internal", "list_email_threads"),
]


def check(role: str):
    cli = OG(role)
    print(f"\n== role={role} ==")
    for graph, query in CHECKS:
        try:
            res = cli.query(graph, query, params={}, branch="main")
            print(f"  {graph}.{query}: ALLOW row_count={res.get('row_count')}")
        except OGError as e:
            print(f"  {graph}.{query}: DENY http={e.status}")


if __name__ == "__main__":
    check("content-agent")
    check("gtm-agent")
