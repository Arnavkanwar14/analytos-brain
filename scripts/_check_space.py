#!/usr/bin/env python3
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ.get("HF_TOKEN"))
info = api.space_info("Arnavkanwar/analytos-brain-v2")
print("sha:", info.sha)
print("stage:", info.runtime.stage if info.runtime else None)
print("hardware:", info.runtime.hardware if info.runtime else None)
print("raw runtime:", info.runtime)
