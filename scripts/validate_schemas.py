#!/usr/bin/env python3
"""Parse/typecheck each .pg by init-ing a throwaway local graph."""
import subprocess, shutil, os, sys

CLUSTER = "/root/analytos-brain/cluster"
TMP = "/tmp/vg"

def main():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)
    rc = 0
    for g in ["knowledge", "market", "internal"]:
        print(f"=== {g} ===", flush=True)
        r = subprocess.run(
            ["omnigraph", "init", "--schema", f"{CLUSTER}/schemas/{g}.pg", f"{TMP}/{g}.omni"],
            capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode != 0:
            print("STDERR:", r.stderr.strip())
            print(f"FAIL:{g}")
            rc = 1
        else:
            print(f"OK:{g}")
    return rc

if __name__ == "__main__":
    sys.exit(main())
