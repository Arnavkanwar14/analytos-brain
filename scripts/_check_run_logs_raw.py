#!/usr/bin/env python3
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ.get("HF_TOKEN"))
lines = []
for entry in api.fetch_space_logs("Arnavkanwar/analytos-brain-v2", build=False, follow=False):
    lines.append(str(entry))
print("total run log lines:", len(lines))
print("---- last 80 ----")
for l in lines[-80:]:
    print(repr(l))
