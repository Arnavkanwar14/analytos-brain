#!/usr/bin/env python3
import re
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

text = Path("/root/analytos-brain/.env").read_text()
m = re.search(r"^HF_TOKEN=(.*)$", text, re.M)
token = m.group(1).strip()
api = HfApi(token=token)

path = hf_hub_download(
    repo_id="Arnavkanwar/analytos-brain-v2",
    repo_type="space",
    filename="hf/start.sh",
    token=token,
    revision="9d62e44dde",
)
content = Path(path).read_text()
print("deployed hf/start.sh length:", len(content))
print("contains '[startup]':", "[startup]" in content)
print("contains 'omnigraph-server.log':", "OMNIGRAPH_LOG_FILE" in content)
print("contains old direct install curl (should be False now):", "curl -fsSL https://raw.githubusercontent.com/ModernRelay/omnigraph" in content and "RUN curl" not in content)
