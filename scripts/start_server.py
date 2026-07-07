#!/usr/bin/env python3
"""Boot omnigraph-server from the cluster with Cedar policy + bearer auth enabled.
Reads secrets from /root/analytos-brain/.env. Runs in the foreground (background it
from the caller). Restart this after any `cluster apply` to pick up changes."""
import os, sys, pathlib

ROOT = pathlib.Path("/root/analytos-brain")
ENV = ROOT / ".env"
CLUSTER = str(ROOT / "cluster")

def load_env():
    env = dict(os.environ)
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def main():
    env = load_env()
    bind = env.get("OMNIGRAPH_BIND", "127.0.0.1:8080")
    if "OMNIGRAPH_SERVER_BEARER_TOKENS_JSON" not in env:
        print("ERROR: tokens not found; run gen_env.py first", file=sys.stderr)
        return 1
    print(f"booting omnigraph-server --cluster {CLUSTER} --bind {bind}", flush=True)
    os.execvpe("omnigraph-server",
               ["omnigraph-server", "--cluster", CLUSTER, "--bind", bind],
               env)

if __name__ == "__main__":
    sys.exit(main())
