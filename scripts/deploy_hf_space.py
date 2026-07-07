#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from huggingface_hub import HfApi


def read_hf_token() -> str:
    text = Path("/root/analytos-brain/.env").read_text()
    match = re.search(r"^HF_TOKEN=(.*)$", text, re.M)
    return match.group(1).strip() if match else ""


def main() -> int:
    token = read_hf_token()
    if not token:
        raise RuntimeError("HF_TOKEN missing in /root/analytos-brain/.env")
    api = HfApi(token=token)
    api.upload_folder(
        repo_id="Arnavkanwar/analytos-brain",
        repo_type="space",
        folder_path="/root/analytos-brain",
        ignore_patterns=[
            ".env",
            ".env.*",
            ".venv/*",
            ".cache/*",
            "cluster/__cluster/*",
            "cluster/graphs/*",
            "runs/*",
            "__pycache__/*",
            "*.pyc",
        ],
    )
    print("uploaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
