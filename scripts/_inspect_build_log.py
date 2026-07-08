#!/usr/bin/env python3
import re
from pathlib import Path
from huggingface_hub import HfApi

text = Path("/root/analytos-brain/.env").read_text()
m = re.search(r"^HF_TOKEN=(.*)$", text, re.M)
token = m.group(1).strip()
api = HfApi(token=token)

lines = []
for entry in api.fetch_space_logs("Arnavkanwar/analytos-brain-v2", build=True, follow=False, token=token):
    lines.append(str(entry))
print("total lines:", len(lines))
print("---- first 40 ----")
for l in lines[:40]:
    print(repr(l))
print("---- last 60 ----")
for l in lines[-60:]:
    print(repr(l))
