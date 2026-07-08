#!/usr/bin/env python3
"""Validate + converge the Analytos Brain cluster. Idempotent (safe to re-run)."""
import os
import subprocess
import sys

CFG = "/root/analytos-brain/cluster"
ACTOR = "act-admin"
STEP_TIMEOUT_SECS = int(os.environ.get("CLUSTER_STEP_TIMEOUT_SECS", "180"))


def step(title, cmd, timeout=STEP_TIMEOUT_SECS):
    print(f"\n===== {title} =====", flush=True)
    print("+", " ".join(cmd), flush=True)
    try:
        r = subprocess.run(cmd, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"!! TIMEOUT: {title} exceeded {timeout}s", flush=True)
        return 124

    if r.returncode != 0:
        print(f"!! FAILED: {title} (rc={r.returncode})", flush=True)
    return r.returncode


def main():
    if step("cluster validate", ["omnigraph", "cluster", "validate", "--config", CFG]):
        return 1

    if os.path.exists(os.path.join(CFG, "__cluster", "state.json")):
        if step("cluster refresh", ["omnigraph", "cluster", "refresh", "--config", CFG]):
            return 1
    else:
        if step("cluster import", ["omnigraph", "cluster", "import", "--config", CFG]):
            return 1

    if step("cluster plan", ["omnigraph", "cluster", "plan", "--config", CFG]):
        return 1
    if step("cluster apply", ["omnigraph", "cluster", "apply", "--config", CFG, "--as", ACTOR]):
        return 1
    if step("cluster status", ["omnigraph", "cluster", "status", "--config", CFG]):
        return 1

    print("\nDONE.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
