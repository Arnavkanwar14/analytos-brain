#!/usr/bin/env python3
"""Create Arnavkanwar/analytos-brain-v3 Space and upload current repo contents."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

REPO_ID = "Arnavkanwar/analytos-brain-v3"


def read_env_var(name: str) -> str:
    text = Path("/root/analytos-brain/.env").read_text()
    match = re.search(rf"^{name}=(.*)$", text, re.M)
    if not match:
        raise RuntimeError(f"{name} missing in /root/analytos-brain/.env")
    return match.group(1).strip()


def main() -> int:
    token = read_env_var("HF_TOKEN")
    api = HfApi(token=token)

    print(f"creating space {REPO_ID} (docker sdk)...")
    try:
        url = api.create_repo(
            repo_id=REPO_ID,
            repo_type="space",
            space_sdk="docker",
            exist_ok=True,
        )
        print("create_repo ok:", url)
    except HfHubHTTPError as e:
        print("create_repo error:", e)
        raise

    print("uploading folder contents...")
    api.upload_folder(
        repo_id=REPO_ID,
        repo_type="space",
        folder_path="/root/analytos-brain",
        ignore_patterns=[
            ".env",
            ".env.*",
            ".venv/*",
            ".cache/*",
            ".git/*",
            "node_modules/*",
            "cluster/__cluster/*",
            "cluster/graphs/*",
            "runs/*",
            "__pycache__/*",
            "*.pyc",
            "outputs/*.log",
        ],
        commit_message="Deploy analytos-brain-v3 (HF localhost hardening + latest main)",
    )
    print("uploaded")

    secret_names = [
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "TOKEN_ADMIN",
        "TOKEN_REVIEWER",
        "TOKEN_CONTENT_AGENT",
        "TOKEN_GTM_AGENT",
        "TOKEN_INGEST",
    ]
    for name in secret_names:
        value = read_env_var(name)
        api.add_space_secret(repo_id=REPO_ID, key=name, value=value)
        print(f"set secret {name}")

    print("triggering rebuild with secrets applied...")
    try:
        api.restart_space(repo_id=REPO_ID, factory_reboot=True)
        print("restart triggered")
    except HfHubHTTPError as e:
        print("restart_space error (non-fatal, initial push may already be building):", e)

    runtime = api.get_space_runtime(REPO_ID)
    print("stage=", runtime.stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
