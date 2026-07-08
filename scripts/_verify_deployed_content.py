#!/usr/bin/env python3
"""Verify the actual deployed hf/start.sh content on the Space matches the
fixed local (GitHub d7aeed1) version, since HF build logs show the Space
repo's OWN commit sha (upload commit), not the upstream GitHub sha."""
import os
from huggingface_hub import hf_hub_download

token = os.environ.get("HF_TOKEN")
path = hf_hub_download(
    repo_id="Arnavkanwar/analytos-brain-v2",
    repo_type="space",
    filename="hf/start.sh",
    token=token,
    force_download=True,
)
deployed = open(path).read()
local = open("/root/analytos-brain/hf/start.sh").read()

print("deployed == local git (d7aeed1) working tree:", deployed == local)
print("deployed contains '[startup]' step logs:", "[startup]" in deployed)
print("deployed contains bounded timeout var (OMNIGRAPH_HEALTH_TIMEOUT_SECS):",
      "OMNIGRAPH_HEALTH_TIMEOUT_SECS" in deployed)
print("deployed contains 'timeout' command usage:", "timeout" in deployed)
print()
print("---- deployed hf/start.sh (first 20 lines) ----")
for line in deployed.splitlines()[:20]:
    print(line)
