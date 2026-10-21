"""Run offline executable checks and retain sanitized, reproducible receipts."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
repo = root.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--ui", action="store_true", help="Open actual native windows with isolated synthetic data.")
parser.add_argument("--regressions", action="store_true", help="Build/test Witness and shared HAL.")
parser.add_argument("--increment", choices=["S03-A", "S03-B"], default="S03-A")
args = parser.parse_args()
out = root / "engineering/s03_first_playable/verification" / args.increment
out.mkdir(parents=True, exist_ok=True)
app = root / "dist/Technical Interview Lab.app/Contents/MacOS/TechnicalInterviewLab"
receipt = {"schema": "tia-verification/v1", "increment": args.increment,
           "source_parent": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
           "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "human_uat": "NOT_RUN", "live_api_uat": "NOT_RUN", "checks": []}

def run(label, command, timeout=180):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=timeout)
        text, code = result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        text, code = "Verification watchdog expired.\n", 124
    text = text.replace(str(repo), "<repo>").replace(str(Path.home()), "<home>")
    (out / (label + ".txt")).write_text(text, encoding="utf-8")
    check = {"name": label, "command": [str(x).replace(str(repo) + "/", "") for x in command],
             "exit_code": code, "status": "PASSED" if code == 0 else "FAILED",
             "elapsed_seconds": round(time.monotonic() - started, 3)}
    found = re.search(r"Ran (\d+) tests in", text)
    if found:
        check["unittest_count"] = int(found.group(1))
    native = re.search(r"Native tests: (\d+) passed, (\d+) failed", text)
    if native:
        check["native_passed"], check["native_failed"] = map(int, native.groups())
    receipt["checks"].append(check)
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(label, check["status"], check["elapsed_seconds"], "seconds", flush=True)
    if code:
        print(text[-4000:], flush=True)
        raise SystemExit(code)

run("python", [sys.executable, "-B", str(root / "run_tests.py")])
run("native-build", ["bash", str(root / "scripts/build_app.sh")])
if args.ui:
    test_dir = root / ".build-cache" / ("verified-ui-" + str(time.time_ns()))
    run("webkit", [str(app), "--ui-self-test", "--test-output", str(test_dir)])
    run("app-recovery", [str(app), "--ui-recovery-test", "--test-output", str(test_dir)])
    for name in ("ui-test-receipt.json", "ui-recovery-receipt.json"):
        shutil.copyfile(test_dir / name, out / name)
    for source, target in (("00.png", "entry.png"), ("05.png", "interview-room.png"), ("07.png", "completion.png")):
        shutil.copyfile(test_dir / source, out / target)
if args.regressions:
    run("witness-hal", ["bash", str(repo / "scripts/verify_witness_local.sh")], timeout=240)
receipt["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt["real_provider_requests_attempted"] = 0
(out / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
print("Verification receipts:", out.relative_to(repo), flush=True)
