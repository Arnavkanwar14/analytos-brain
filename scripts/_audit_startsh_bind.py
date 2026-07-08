#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from huggingface_hub import hf_hub_download

text = Path("/root/analytos-brain/.env").read_text()
token = re.search(r"^HF_TOKEN=(.*)$", text, re.M).group(1).strip()

for repo in ["Arnavkanwar/analytos-brain", "Arnavkanwar/analytos-brain-v3"]:
    path = hf_hub_download(
        repo_id=repo,
        repo_type="space",
        filename="hf/start.sh",
        token=token,
        revision="main",
    )
    content = Path(path).read_text()
    print(f"==== {repo} ====")
    for i, line in enumerate(content.splitlines(), 1):
        if any(
            x in line
            for x in ["BIND", "bind", "0.0.0.0", "8080", "curl", "install", "uvicorn", "PORT"]
        ):
            print(f"{i}: {line}")
