#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from huggingface_hub import HfApi


SPACE_ID = "Arnavkanwar/analytos-brain"
ENV_PATH = Path("/root/analytos-brain/.env")


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> int:
    env = load_env()
    token = env.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN missing in .env")
    api = HfApi(token=token)

    keys = [
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "TOKEN_ADMIN",
        "TOKEN_REVIEWER",
        "TOKEN_CONTENT_AGENT",
        "TOKEN_GTM_AGENT",
        "TOKEN_INGEST",
    ]
    for key in keys:
        val = env.get(key, "")
        if val:
            api.add_space_secret(repo_id=SPACE_ID, key=key, value=val)
            print(f"set secret: {key}")
        else:
            print(f"skip empty secret: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
