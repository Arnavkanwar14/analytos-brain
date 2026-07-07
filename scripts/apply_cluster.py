#!/usr/bin/env python3
"""Validate + converge the Analytos Brain cluster. Idempotent (safe to re-run)."""
import subprocess, sys

CFG = "/root/analytos-brain/cluster"
ACTOR = "act-admin"

def step(title, cmd):
    print(f"\n===== {title} =====", flush=True)
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print("STDERR:", r.stderr.strip())
        print(f"!! FAILED: {title} (rc={r.returncode})")
    return r.returncode

def main():
    if step("cluster validate", ["omnigraph", "cluster", "validate", "--config", CFG]):
        return 1
    # first run needs `import` (creates the state ledger); later runs need `refresh`.
    import os
    if os.path.exists(os.path.join(CFG, "__cluster", "state.json")):
        step("cluster refresh", ["omnigraph", "cluster", "refresh", "--config", CFG])
    else:
        step("cluster import", ["omnigraph", "cluster", "import", "--config", CFG])
    step("cluster plan", ["omnigraph", "cluster", "plan", "--config", CFG])
    if step("cluster apply", ["omnigraph", "cluster", "apply", "--config", CFG, "--as", ACTOR]):
        return 1
    step("cluster status", ["omnigraph", "cluster", "status", "--config", CFG])
    print("\nDONE.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
