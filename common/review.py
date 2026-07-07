"""HITL review actions: approve (merge branch -> main, human actor) or reject
(discard branch). Updates the run manifest. Shared by the CLI and the backend."""
from __future__ import annotations
import contextlib
import datetime
import fcntl
import json
import os
import pathlib
import random
import time

from .og import OG, OGError

RUNS = pathlib.Path("/root/analytos-brain/runs")
LOCKS = RUNS / ".locks"
_CONCURRENT_ERROR_MARKERS = ("Concurrent modification", "table version")


def load_manifest(run_id: str) -> dict:
    return json.loads((RUNS / f"{run_id}.json").read_text())


def save_manifest(m: dict):
    (RUNS / f"{m['run_id']}.json").write_text(json.dumps(m, indent=2))


@contextlib.contextmanager
def _run_merge_lock(run_id: str):
    """Serialize approve/merge for a run across concurrent UI requests."""
    LOCKS.mkdir(parents=True, exist_ok=True)
    lock_path = LOCKS / f"{run_id}.merge.lock"
    with lock_path.open("w") as fd:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def _target_merge_lock(graph: str, target: str = "main"):
    """Serialize merges that target the same graph branch across all runs."""
    LOCKS.mkdir(parents=True, exist_ok=True)
    lock_path = LOCKS / f"{graph}.{target}.target.lock"
    with lock_path.open("w") as fd:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


def _is_concurrent_merge_error(exc: OGError) -> bool:
    txt = str(exc).lower()
    return any(marker.lower() in txt for marker in _CONCURRENT_ERROR_MARKERS)


def _merge_with_retry(admin: OG, graph: str, source: str, target: str = "main", attempts: int | None = None) -> tuple[dict, int]:
    """Retry transient concurrent-modification errors with bounded jitter backoff."""
    if attempts is None:
        # HF Spaces can briefly contend with Omnigraph recovery writes after ingest.
        # Use a longer retry window there; keep local retries snappy.
        attempts = 10 if os.getenv("SPACE_ID") else 5
    retries = 0
    for i in range(attempts):
        try:
            return admin.merge(graph, source, target), retries
        except OGError as exc:
            if not _is_concurrent_merge_error(exc) or i == attempts - 1:
                raise
            retries += 1
            # Keep retries short so UI flow remains responsive while smoothing contention.
            time.sleep(min(0.2 * (2 ** i), 2.5) + random.uniform(0.0, 0.12))
    raise RuntimeError("unreachable")


def list_runs() -> list[dict]:
    out = []
    for p in sorted(RUNS.glob("run-*.json")) + sorted(RUNS.glob("*.json")):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        out.append({"run_id": m.get("run_id"), "status": m.get("status"),
                    "created_at": m.get("created_at"), "docs": m.get("docs", []),
                    "graphs": m.get("graphs", []), "branch": m.get("branch"),
                    "approved_by": m.get("approved_by"), "rejected_by": m.get("rejected_by"),
                    "counts": {g: d.get("counts", {}) for g, d in (m.get("diffs") or {}).items()}})
    # de-dupe by run_id (glob overlap), keep last
    seen = {}
    for r in out:
        seen[r["run_id"]] = r
    return sorted(seen.values(), key=lambda r: r.get("created_at") or "", reverse=True)


def approve(run_id: str, actor_role: str = "admin") -> dict:
    """Merge every ingest branch for this run into main, as a human actor."""
    with _run_merge_lock(run_id):
        m = load_manifest(run_id)
        if m.get("status") == "approved":
            return m
        admin = OG(actor_role)
        results = {}
        retry_counts = {}
        for g in m["graphs"]:
            counts = ((m.get("diffs") or {}).get(g) or {}).get("counts", {})
            has_changes = any((counts.get(k, 0) or 0) > 0 for k in ("added_nodes", "changed_nodes", "added_edges"))
            if not has_changes:
                # No-op ingest branches are common in hosted demos (same seed docs ingested repeatedly).
                # Skipping merge avoids unnecessary optimistic-commit contention on the target branch.
                results[g] = {"skipped": True, "reason": "no-op diff"}
                retry_counts[g] = 0
                continue
            # Run-level lock avoids duplicate approvals; target lock prevents
            # cross-run write races on the same graph:main branch.
            with _target_merge_lock(g, "main"):
                res, retries = _merge_with_retry(admin, g, m["branch"], "main")
            results[g] = res
            retry_counts[g] = retries
        m["status"] = "approved"
        m["approved_by"] = f"act-{actor_role}"
        m["approved_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        m["merge_results"] = results
        m["merge_retry_counts"] = retry_counts
        m["merge_retried"] = any(v > 0 for v in retry_counts.values())
        save_manifest(m)
        return m


def reject(run_id: str, actor_role: str = "admin") -> dict:
    """Discard every ingest branch for this run (nothing reaches main)."""
    m = load_manifest(run_id)
    admin = OG(actor_role)
    for g in m["graphs"]:
        try:
            admin.delete_branch(g, m["branch"])
        except Exception as e:
            print(f"  [warn] delete {g}:{m['branch']} -> {e}")
    m["status"] = "rejected"
    m["rejected_by"] = f"act-{actor_role}"
    m["rejected_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_manifest(m)
    return m
