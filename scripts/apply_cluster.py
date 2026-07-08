#!/usr/bin/env python3
"""Validate + converge the Analytos Brain cluster. Idempotent (safe to re-run)."""
import os
import subprocess
import sys

CFG = "/root/analytos-brain/cluster"
ACTOR = "act-admin"
BAKED_MARKER = "/root/analytos-brain/.hf-baked"
STEP_TIMEOUT_SECS = int(os.environ.get("CLUSTER_STEP_TIMEOUT_SECS", "180"))


def is_hf_space() -> bool:
    return (
        os.environ.get("HF_SPACE") == "1"
        or bool(os.environ.get("SPACE_ID"))
        or os.environ.get("PORT") == "7860"
    )


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

    if is_hf_space() and os.path.exists(BAKED_MARKER):
        print("HF Space: image-baked cluster present; skipping import/plan/apply", flush=True)
        return 0

    state_path = os.path.join(CFG, "__cluster", "state.json")
    if os.path.exists(state_path):
        if step("cluster refresh", ["omnigraph", "cluster", "refresh", "--config", CFG]):
            return 1
    else:
        if step("cluster import", ["omnigraph", "cluster", "import", "--config", CFG]):
            return 1

    if is_hf_space():
        hf_timeout = int(os.environ.get("HF_CLUSTER_APPLY_TIMEOUT_SECS", "45"))
        if step("cluster plan", ["omnigraph", "cluster", "plan", "--config", CFG], timeout=hf_timeout):
            return 1
        if step(
            "cluster apply",
            ["omnigraph", "cluster", "apply", "--config", CFG, "--as", ACTOR],
            timeout=hf_timeout,
        ):
            return 1
        print("HF Space: cluster apply complete (status skipped for speed)", flush=True)
        return 0

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
