#!/usr/bin/env python3
"""Idempotent system-package bootstrap for the Analytos Brain POC (run as root in WSL Ubuntu)."""
import subprocess, sys, shutil

def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, **kw)

def have(cmd):
    return shutil.which(cmd)

APT_PKGS = ["python3-pip", "python3-venv", "unzip", "ca-certificates", "curl", "git", "jq"]

def main():
    run(["apt-get", "update", "-y"])
    run(["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", *APT_PKGS])

    # Node.js LTS via NodeSource (Linux node, not the Windows /mnt/c one)
    if not have("node") or "/mnt/c" in (have("node") or ""):
        run(["bash", "-lc", "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -"])
        run(["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", "nodejs"])

    print("\n==== VERSIONS ====", flush=True)
    for c in ["python3", "pip3", "node", "npm", "git", "curl", "unzip", "jq"]:
        p = have(c)
        v = ""
        if p:
            try:
                v = subprocess.run([c, "--version"], capture_output=True, text=True).stdout.strip().splitlines()[0]
            except Exception as e:
                v = f"(version check failed: {e})"
        print(f"{c}: {p or 'MISSING'}  {v}")

if __name__ == "__main__":
    sys.exit(main())
