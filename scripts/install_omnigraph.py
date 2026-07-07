#!/usr/bin/env python3
"""Install the Omnigraph engine (CLI + server) from published release binaries, run as root."""
import os, subprocess, sys, shutil

HOME = os.path.expanduser("~")
LOCAL_BIN = os.path.join(HOME, ".local", "bin")

def run(cmd, **kw):
    print("+", cmd if isinstance(cmd, str) else " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, **kw)

def main():
    # Official installer: downloads omnigraph-linux-x86_64.tar.gz -> ~/.local/bin
    run(["bash", "-lc",
         "curl -fsSL https://raw.githubusercontent.com/ModernRelay/omnigraph/main/scripts/install.sh | bash"])

    # Symlink onto global PATH so every later shell finds them without PATH juggling.
    for b in ["omnigraph", "omnigraph-server"]:
        src = os.path.join(LOCAL_BIN, b)
        dst = os.path.join("/usr/local/bin", b)
        if os.path.exists(src):
            if os.path.islink(dst) or os.path.exists(dst):
                os.remove(dst)
            os.symlink(src, dst)
            print(f"symlinked {dst} -> {src}")
        else:
            print(f"WARNING: {src} not found after install")

    print("\n==== OMNIGRAPH VERSIONS ====", flush=True)
    for b in ["omnigraph", "omnigraph-server"]:
        p = shutil.which(b)
        print(f"{b}: {p or 'MISSING'}")
        if p:
            subprocess.run([b, "version"], check=False)

if __name__ == "__main__":
    sys.exit(main())
