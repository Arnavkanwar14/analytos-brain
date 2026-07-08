#!/usr/bin/env python3
"""Poll a Hugging Face Space's runtime status until it settles, printing
stage transitions and periodic build/container log tails.
"""
import os
import sys
import time
from datetime import datetime, timezone

from huggingface_hub import HfApi

REPO_ID = "Arnavkanwar/analytos-brain-v2"
POLL_SECS = 17
MAX_SECS = int(os.environ.get("MONITOR_MAX_SECS", 8 * 60))

def ts():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def main():
    token = os.environ.get("HF_TOKEN")
    api = HfApi(token=token)
    start = time.time()
    last_stage = None
    last_sha = None

    while True:
        elapsed = time.time() - start
        try:
            info = api.space_info(REPO_ID)
            runtime = info.runtime
            stage = getattr(runtime, "stage", None)
            sha = getattr(info, "sha", None)
        except Exception as e:
            print(f"[{ts()}] ERROR fetching space_info: {e}")
            time.sleep(POLL_SECS)
            continue

        if stage != last_stage or sha != last_sha:
            print(f"[{ts()}] elapsed={elapsed:0.0f}s stage={stage} sha={sha}")
            last_stage = stage
            last_sha = sha
        else:
            print(f"[{ts()}] elapsed={elapsed:0.0f}s stage={stage} (unchanged) sha={sha}")

        if stage == "RUNNING":
            print(f"[{ts()}] Space is RUNNING. Exiting monitor loop.")
            return 0
        if stage in ("RUNTIME_ERROR", "BUILD_ERROR", "DELETED", "PAUSED"):
            print(f"[{ts()}] Space entered terminal/error stage: {stage}")
            return 1
        if elapsed > MAX_SECS:
            print(f"[{ts()}] Exceeded max monitor window ({MAX_SECS}s) while stage={stage}")
            return 2

        time.sleep(POLL_SECS)

if __name__ == "__main__":
    sys.exit(main())
