#!/usr/bin/env python3
"""
Comprehensive poller for Arnavkanwar/analytos-brain-v2 factory rebuild.

- Polls runtime stage every ~20-30s for up to ~8 minutes.
- Confirms build log shows the expected commit SHA.
- Watches runtime logs for progression past "===== Application Startup ====="
  looking for new "[startup] ..." lines and "Uvicorn running on".
- Stops early on RUNNING or on a new specific error.
"""
import re
import sys
import time
from pathlib import Path
from huggingface_hub import HfApi

REPO_ID = "Arnavkanwar/analytos-brain-v2"
EXPECTED_SHA = "d7aeed1"
OLD_SHA = "c3deaf1"
TOTAL_MINUTES = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
POLL_SECONDS = 25

text = Path("/root/analytos-brain/.env").read_text()
m = re.search(r"^HF_TOKEN=(.*)$", text, re.M)
token = m.group(1).strip()
api = HfApi(token=token)

deadline = time.time() + 60 * TOTAL_MINUTES
last_stage = None
sha_confirmed = None
seen_startup_lines = set()
saw_app_startup_banner = False
saw_uvicorn = False
final_error_line = None

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def check_build_logs():
    global sha_confirmed
    try:
        lines = []
        for entry in api.fetch_space_logs(REPO_ID, build=True, follow=False, token=token):
            lines.append(str(entry))
        joined = "\n".join(lines[-500:])
        if EXPECTED_SHA in joined:
            sha_confirmed = True
            log(f"BUILD LOG: found expected commit {EXPECTED_SHA}")
        elif OLD_SHA in joined:
            sha_confirmed = False
            log(f"BUILD LOG: still shows OLD commit {OLD_SHA} (no {EXPECTED_SHA} yet)")
        else:
            # search more broadly for any 7-char hex that looks like a commit ref
            log("BUILD LOG: neither expected nor old SHA string found in tail of build log")
        return lines
    except Exception as e:
        log(f"build log fetch err: {e!r}")
        return []

def check_run_logs():
    global saw_app_startup_banner, saw_uvicorn, final_error_line
    try:
        lines = []
        for entry in api.fetch_space_logs(REPO_ID, build=False, follow=False, token=token):
            lines.append(str(entry))
        tail = lines[-400:]
        for line in tail:
            if "Application Startup" in line:
                saw_app_startup_banner = True
            if "[startup]" in line and line not in seen_startup_lines:
                seen_startup_lines.add(line)
                log(f"RUN LOG [startup]: {line.strip()}")
            if "Uvicorn running on" in line:
                saw_uvicorn = True
            low = line.lower()
            if any(k in low for k in ["traceback", "error", "exception", "failed", "fatal"]):
                final_error_line = line.strip()
        return lines
    except Exception as e:
        log(f"run log fetch err: {e!r}")
        return []

log(f"Starting poll loop for {REPO_ID}, target sha={EXPECTED_SHA}, up to {TOTAL_MINUTES} min")

runtime = api.get_space_runtime(REPO_ID)
while time.time() < deadline:
    runtime = api.get_space_runtime(REPO_ID)
    if runtime.stage != last_stage:
        log(f"stage change -> {runtime.stage}")
        last_stage = runtime.stage

    if sha_confirmed is None or sha_confirmed is False:
        check_build_logs()

    check_run_logs()

    if runtime.stage == "RUNNING":
        log("Stage is RUNNING. Stopping poll loop.")
        break
    if runtime.stage in ("RUNTIME_ERROR", "BUILD_ERROR", "PAUSED", "DELETED"):
        log(f"Stage is terminal/error state: {runtime.stage}. Stopping poll loop.")
        break

    time.sleep(POLL_SECONDS)

print("\n===== SUMMARY =====")
print("final_stage=", runtime.stage)
print("sha_confirmed_new=", sha_confirmed)
print("saw_app_startup_banner=", saw_app_startup_banner)
print("saw_startup_step_logs=", len(seen_startup_lines) > 0, f"(count={len(seen_startup_lines)})")
print("saw_uvicorn_running=", saw_uvicorn)
print("last_error_like_line=", final_error_line)

print("\n---- run log tail (last 60 lines) ----")
final_run_logs = check_run_logs()
for line in final_run_logs[-60:]:
    print(line)
