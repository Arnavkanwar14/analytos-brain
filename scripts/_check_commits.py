#!/usr/bin/env python3
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ.get("HF_TOKEN"))
commits = api.list_repo_commits("Arnavkanwar/analytos-brain-v2", repo_type="space")
for c in commits[:8]:
    print(c.commit_id, "|", c.title, "|", c.created_at)
