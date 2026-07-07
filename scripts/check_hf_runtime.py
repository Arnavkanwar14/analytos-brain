#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from huggingface_hub import HfApi


def main() -> int:
    text = Path("/root/analytos-brain/.env").read_text()
    token = re.search(r"^HF_TOKEN=(.*)$", text, re.M).group(1).strip()
    api = HfApi(token=token)
    runtime = api.get_space_runtime("Arnavkanwar/analytos-brain")
    print("stage=", runtime.stage)
    print("runtime=", runtime)
    try:
        print("raw=", runtime.raw)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
