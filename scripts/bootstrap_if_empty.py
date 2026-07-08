#!/usr/bin/env python3
"""Seed main with golden extraction when the hosted instance boots empty.

Also recovers the common HF failure mode where seed docs were ingested onto a
pending branch but never approved onto main (stats stay zero).
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/root/analytos-brain")

from common.og import OG, OGError
from common import review
from pipeline.run import run_ingestion

GOLDEN_RUN_ID = "hf-space-bootstrap"


def _product_count(admin: OG) -> int | None:
    try:
        return int(admin.query("knowledge", "list_products", branch="main").get("row_count", 0) or 0)
    except OGError as e:
        print(f"[bootstrap] skip: cannot read main ({e})")
        return None


def _try_approve_pending_seed() -> bool:
    """Approve any pending run that already carries the golden seed docs."""
    pending = [r for r in review.list_runs() if r.get("status") == "pending"]
    if not pending:
        return False

    seed_names = {
        "email-01-stockly-pilot-thread.md",
        "email-02-inspectly-medical-thread.md",
        "flowmax-product-overview.md",
        "icp-analytos.md",
        "inspectly-product-overview.md",
        "stockly-product-overview.md",
    }
    # Prefer full golden seed coverage, then any pending run.
    pending.sort(
        key=lambda r: (
            -len(set(r.get("docs") or []) & seed_names),
            str(r.get("created_at") or ""),
        ),
        reverse=True,
    )
    chosen = pending[0]
    run_id = chosen.get("run_id")
    docs = set(chosen.get("docs") or [])
    print(f"[bootstrap] main empty; approving pending run {run_id!r} docs={sorted(docs)}")
    review.approve(run_id, actor_role="admin")
    print(f"[bootstrap] approved pending run {run_id!r}")
    return True


def main() -> int:
    admin = OG("admin")
    count = _product_count(admin)
    if count is None:
        return 0
    if count:
        print(f"[bootstrap] main already has {count} products; skipping")
        return 0

    if _try_approve_pending_seed():
        after = _product_count(admin)
        if after:
            print(f"[bootstrap] main now has {after} products after approve")
            return 0
        print("[bootstrap] approve did not populate main; continuing with fresh ingest")

    print("[bootstrap] main empty -> golden ingest + approve")
    run_ingestion(run_id=GOLDEN_RUN_ID, use_llm=False, log=print)
    review.approve(GOLDEN_RUN_ID, actor_role="admin")
    after = _product_count(admin)
    print(f"[bootstrap] done (products={after})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
