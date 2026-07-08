#!/usr/bin/env python3
import re
from pathlib import Path
from huggingface_hub import HfApi

text = Path("/root/analytos-brain/.env").read_text()
m = re.search(r"^HF_TOKEN=(.*)$", text, re.M)
token = m.group(1).strip()
api = HfApi(token=token)

lines = []
for entry in api.fetch_space_logs("Arnavkanwar/analytos-brain-v2", build=False, follow=False, token=token):
    lines.append(str(entry))
print("total lines:", len(lines))
for l in lines[-80:]:
    print(repr(l))
