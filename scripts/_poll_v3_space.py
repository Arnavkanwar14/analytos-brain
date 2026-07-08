#!/usr/bin/env python3
"""Poll Arnavkanwar/analytos-brain-v3 runtime status until RUNNING or terminal failure."""
from __future__ import annotations

import re
import time
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "Arnavkanwar/analytos-brain-v3"
TERMINAL_OK = {"RUNNING"}
TERMINAL_BAD = {"RUNTIME_ERROR", "BUILD_ERROR", "PAUSED", "DELETED", "APP_STARTING_ERROR"}
MAX_SECONDS = 480
POLL_EVERY = 15


def read_token() -> str:
    text = Path("/root/analytos-brain/.env").read_text()
    return re.search(r"^HF_TOKEN=(.*)$", text, re.M).group(1).strip()


def main() -> int:
    api = HfApi(token=read_token())
    start = time.time()
    last_stage = None
    while time.time() - start < MAX_SECONDS:
        runtime = api.get_space_runtime(REPO_ID)
        stage = runtime.stage
        elapsed = int(time.time() - start)
        if stage != last_stage:
            print(f"[{elapsed}s] stage={stage}")
            last_stage = stage
        else:
            print(f"[{elapsed}s] stage={stage} (unchanged)")
        if stage in TERMINAL_OK:
            print("REACHED RUNNING")
            return 0
        if stage in TERMINAL_BAD:
            print("TERMINAL FAILURE STAGE:", stage)
            return 1
        time.sleep(POLL_EVERY)
    print("TIMED OUT waiting for RUNNING, last stage:", last_stage)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
