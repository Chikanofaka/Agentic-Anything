"""C2C real macOS AppKit/WebKit + ephemeral Postgres + URLProtocol-only acceptance.

Runs three isolated App invocations (positive, stale-code and restart). The host
owns each evidence receipt. This runner never activates a live network adapter.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
APP = ROOT / "dist/Technical Interview Lab.app/Contents/MacOS/TechnicalInterviewLab"
DEST = ROOT / "engineering/e4c2c_adaptive/verification_C2C"


def require_postgres():
    # This is the same fixed-list allowlist as the existing Host grade runner.
    sys.path.insert(0, str(ROOT))
    from tia_runtime.grading_binding import find_approved_pg_config, GradingBindingError
    from tia_runtime.sql_accuracy import _postgres_bins, AccuracyError
    try:
        config = find_approved_pg_config()
        _postgres_bins(config)
    except (GradingBindingError, AccuracyError) as error:
        raise SystemExit("C2C_BLOCKED_POSTGRES_NOT_AVAILABLE: " + str(error)) from None
    return config


def run_case(mode, directory, flags, expected, minimum_steps):
    cmd = [str(APP), flags, "--test-output", str(directory)]
    try:
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=240)
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as error:
        output = "C2C_CASE_TIMEOUT\n"
        proc = subprocess.CompletedProcess(cmd, 124, output, "")
    # Only test labels and mock data are printed by the native driver.
    (DEST / (mode + ".log")).write_text(output.replace(str(Path.home()), "<home>"), encoding="utf-8")
    receipt_path = directory / ("ui-adaptive-" + ("receipt" if mode == "positive" else mode + "-receipt") + ".json")
    if proc.returncode != 0 or not receipt_path.is_file():
        raise RuntimeError(mode + ": native test failed (exit " + str(proc.returncode) + ")")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("failed") != 0 or receipt.get("passed", 0) < minimum_steps
            or receipt.get("mock_http_requests") != expected
            or receipt.get("transport") != "MOCK_HTTP"
            or receipt.get("real_credentials_used") is not False
            or receipt.get("api_requests") != 0
            or receipt.get("adaptive_mode") != mode.upper()):
        raise RuntimeError(mode + ": invalid test receipt")
    copy = DEST / (mode + "-receipt.json")
    shutil.copyfile(receipt_path, copy)
    for screenshot in sorted(directory.glob("adaptive-*.png")):
        shutil.copyfile(screenshot, DEST / (mode + "-" + screenshot.name))
    return {"mode": mode, "passed_steps": receipt["passed"], "mock_http_requests": expected,
            "receipt_sha256": hashlib.sha256(copy.read_bytes()).hexdigest(),
            "exit_code": proc.returncode, "real_requests": 0}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    if not APP.is_file():
        raise SystemExit("C2C_BLOCKED_APP_NOT_BUILT: run build_app.sh first")
    config = require_postgres()
    stamp = {"schema": "tia-c2c-verification/v1", "status": "INCOMPLETE",
             "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "app_sha256": hashlib.sha256(APP.read_bytes()).hexdigest(),
             "python_version": sys.version.split()[0],
             "macos": subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip(),
             "postgres_config": Path(config).name, "human_uat": "NOT_RUN", "live_api_uat": "NOT_RUN",
             "cases": []}
    with tempfile.TemporaryDirectory(prefix="tia-c2c-", dir=ROOT / ".build-cache") as root:
        work = Path(root)
        pos = work / "positive"
        stale = work / "stale"
        stamp["cases"].append(run_case("positive", pos, "--ui-adaptive-test", expected=6, minimum_steps=9))
        stamp["cases"].append(run_case("stale", stale, "--ui-adaptive-stale-test", expected=4, minimum_steps=8))
        # A recovery launch reuses ONLY the prior synthetic-data directory.
        stamp["cases"].append(run_case("recovery", pos, "--ui-adaptive-recovery-test", expected=0, minimum_steps=2))
    stamp["status"] = "PASS"
    stamp["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (DEST / "receipt.json").write_text(json.dumps(stamp, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print("C2C_ADAPTIVE_MOCK_UI_GATE=PASS")
    print("C2C case counts: positive 6 MOCK_HTTP, stale 4 MOCK_HTTP, recovery 0 HTTP; 0 live requests")
    print("Receipts:", DEST.relative_to(REPO))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print("C2C_ADAPTIVE_MOCK_UI_GATE=FAILED:", str(error), file=sys.stderr)
        raise SystemExit(1)
