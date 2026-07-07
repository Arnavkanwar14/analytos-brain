#!/usr/bin/env python3
"""Seed main with golden extraction when the hosted instance boots empty."""
from __future__ import annotations

import sys

sys.path.insert(0, "/root/analytos-brain")

from common.og import OG, OGError
from common import review
from pipeline.run import run_ingestion


def main() -> int:
    admin = OG("admin")
    try:
        count = admin.query("knowledge", "list_products", branch="main").get("row_count", 0)
    except OGError as e:
        print(f"[bootstrap] skip: cannot read main ({e})")
        return 0
    if count:
        print(f"[bootstrap] main already has {count} products; skipping")
        return 0
    print("[bootstrap] main empty -> golden ingest + approve")
    run_ingestion(run_id="hf-space-bootstrap", use_llm=False, log=print)
    review.approve("hf-space-bootstrap", actor_role="admin")
    print("[bootstrap] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
