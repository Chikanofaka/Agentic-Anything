#!/bin/bash
# Runs automated tests and stages an UNSIGNED PRIVATE engineering release candidate.
# No human UAT, public push, paid calls, notarization or publication.
set -euo pipefail
REPO="${1:-$HOME/Developer/Agentic-Anything-tia-evaluator}"
ROOT="$REPO/integrations/virtual_technical_interviewer"
OUT="$HOME/Downloads/TIA_Closeout_Engineering_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"
chmod 700 "$OUT"
cd "$ROOT"
node --check ui/app.js
node "$ROOT/tests/test_evaluator_closeout.js" > "$OUT/closeout_tests.log" 2>&1 || { tail -n 80 "$OUT/closeout_tests.log"; exit 1; }
python3 -B -m unittest discover -s tests -p test_evaluator_full_scheme.py > "$OUT/scheme_tests.log" 2>&1 || { tail -n 80 "$OUT/scheme_tests.log"; exit 1; }
python3 -B run_tests.py > "$OUT/python_regression.log" 2>&1 || { tail -n 80 "$OUT/python_regression.log"; exit 1; }
python3 -B scripts/verify_app.py --increment S03-E3D --ui --evaluator --run-label "e4e5_closed_loop_$(date -u +%Y%m%dT%H%M%S)" > "$OUT/native_webkit.log" 2>&1 || { tail -n 80 "$OUT/native_webkit.log"; exit 1; }
python3 -B - "$ROOT/ui/app.js" "$OUT/GATE_RECEIPT.json" <<'PY'
import hashlib,json,sys
from pathlib import Path
src=Path(sys.argv[1]);output=Path(sys.argv[2])
receipt={'schema':'tia-e4e5-automated-gate/v1',
         'status':'AUTOMATED_ENGINEERING_PASS', 'human_uat':'NOT_RUN',
         'app_js_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
         'paid_model_calls':0,'source':'local_mac_automated_tests'}
output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');output.chmod(0o600)
PY
python3 -B "$ROOT/scripts/private_release_candidate.py" --repo "$REPO" --gate-receipt "$OUT/GATE_RECEIPT.json" --output "$OUT/private_candidate"
tail -n 5 "$OUT/python_regression.log"
tail -n 14 "$OUT/native_webkit.log"
echo "TIA_E4_E5_AUTOMATED_GATE=PASS HUMAN_UAT=NOT_RUN PAID_REQUESTS=0"
echo "PRIVATE_ENGINEERING_HANDOFF=$OUT"
