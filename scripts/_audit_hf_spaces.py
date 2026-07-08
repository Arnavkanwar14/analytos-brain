#!/usr/bin/env python3
"""One-off audit: compare deployed HF Space start.sh and runtime stage."""
from __future__ import annotations

import re
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path("/root/analytos-brain")
text = (ROOT / ".env").read_text()
token = re.search(r"^HF_TOKEN=(.*)$", text, re.M).group(1).strip()
api = HfApi(token=token)

for repo in ["Arnavkanwar/analytos-brain-v3", "Arnavkanwar/analytos-brain"]:
    info = api.space_info(repo)
    stage = info.runtime.stage if info.runtime else None
    print(f"\n=== {repo} ===")
    print(f"sha={info.sha} stage={stage}")
    if info.runtime and info.runtime.stage == "PAUSED":
        print(f"runtime={info.runtime}")
    try:
        path = hf_hub_download(
            repo_id=repo,
            repo_type="space",
            filename="hf/start.sh",
            token=token,
            revision="main",
        )
        content = Path(path).read_text()
        for needle in ["OMNIGRAPH_BIND", "0.0.0.0", "curl -fsSL", "install.sh", "HF_SPACE"]:
            print(f"  {needle!r}: {needle in content}")
    except Exception as exc:
        print(f"  start.sh fetch error: {exc}")
