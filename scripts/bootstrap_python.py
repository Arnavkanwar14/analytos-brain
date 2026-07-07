#!/usr/bin/env python3
"""Copy seed docs into the repo and build the Python venv with pipeline/backend deps."""
import os, shutil, subprocess, sys, pathlib

ROOT = pathlib.Path("/root/analytos-brain")
SEED_DST = ROOT / "seed-data"
VENV = ROOT / ".venv"
SRC = pathlib.Path(
    "/mnt/c/Users/bifro/OneDrive/Desktop/"
    "AI Engineer (Omnigraph) task seed data-20260707T062133Z-3-001/"
    "AI Engineer (Omnigraph) task seed data"
)
FILES = [
    "stockly-product-overview.md",
    "inspectly-product-overview.md",
    "icp-analytos.md",
    "email-01-stockly-pilot-thread.md",
    "email-02-inspectly-medical-thread.md",
]
DEPS = [
    "fastapi",
    "uvicorn[standard]",
    "requests",
    "python-dotenv",
    "pydantic",
    "google-genai",  # new unified Gemini SDK: `from google import genai`
]

def main():
    SEED_DST.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        s = SRC / f
        if not s.exists():
            print(f"MISSING seed file: {s}")
            return 1
        shutil.copyfile(s, SEED_DST / f)
        print(f"copied {f} ({(SEED_DST / f).stat().st_size} bytes)")

    if not VENV.exists():
        print("creating venv...", flush=True)
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    pip = str(VENV / "bin" / "pip")
    subprocess.run([pip, "install", "--upgrade", "pip"], check=True)
    print("installing deps...", flush=True)
    subprocess.run([pip, "install", *DEPS], check=True)
    print("\nDONE. venv:", VENV)
    return 0

if __name__ == "__main__":
    sys.exit(main())
