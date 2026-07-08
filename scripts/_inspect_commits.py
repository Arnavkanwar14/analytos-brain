#!/usr/bin/env python3
import re
from pathlib import Path
from huggingface_hub import HfApi

text = Path("/root/analytos-brain/.env").read_text()
m = re.search(r"^HF_TOKEN=(.*)$", text, re.M)
token = m.group(1).strip()
api = HfApi(token=token)

print("---- HF Space repo commits (most recent first) ----")
try:
    commits = api.list_repo_commits("Arnavkanwar/analytos-brain-v2", repo_type="space", token=token)
    for c in commits[:15]:
        print(c.commit_id[:10], c.created_at, "-", c.title)
except Exception as e:
    print("err:", repr(e))
