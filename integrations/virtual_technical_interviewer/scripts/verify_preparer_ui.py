"""Isolated C1B.2 Mac UI test: no live provider, no user credentials."""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / 'dist/Technical Interview Lab.app/Contents/MacOS/TechnicalInterviewLab'
OUT = ROOT / 'engineering/e4c1b_preparer/verification_C1B2'
OUT.mkdir(parents=True, exist_ok=True)

if not APP.is_file():
    raise SystemExit('HOLD: build App before running UI preparer test')

with tempfile.TemporaryDirectory(prefix='tia-c1b2-mock-ui-') as temp:
    try:
        run = subprocess.run([str(APP), '--ui-preparer-test', '--test-output', temp],
                             timeout=150, capture_output=True, text=True, check=False)
    except subprocess.TimeoutExpired:
        raise SystemExit('FAIL: isolated preparer UI watchdog expired')
    raw = run.stdout + run.stderr
    # Synthetic log only; never collect real credentials or personal questions.
    (OUT / 'ui-preparer-stdout.txt').write_text(raw, encoding='utf-8')
    receipt_path = pathlib.Path(temp) / 'ui-preparer-receipt.json'
    if run.returncode != 0 or not receipt_path.is_file():
        print(raw[-3500:], file=sys.stderr)
        raise SystemExit('FAIL: Native preparer UI test did not complete')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    expected = {'passed': 9, 'failed': 0, 'transport': 'MOCK_HTTP',
                'api_requests': 0, 'mock_http_requests': 1,
                'real_credentials_used': False,
                'synthetic_credential_fixture_used': True,
                'human_uat': 'NOT_RUN'}
    if not all(receipt.get(k) == v for k,v in expected.items()):
        raise SystemExit(f'FAIL: C1B2 receipt mismatch: {[k for k,v in expected.items() if receipt.get(k)!=v]}')
    if len(receipt.get('tests', [])) != 9 or any(x.get('status') != 'PASSED' for x in receipt['tests']):
        raise SystemExit('FAIL: C1B2 step receipt incomplete')
    text = json.dumps(receipt)
    if 'C1B2-PRIVATE-REFERENCE' in text:
        raise SystemExit('FAIL: C1B2 reference leaked into receipt')
    (OUT / 'ui-preparer-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')
    for shot in sorted(pathlib.Path(temp).glob('preparer-*.png')):
        (OUT / shot.name).write_bytes(shot.read_bytes())
    print('C1B2_NATIVE_WEBKIT_MOCK_GATE=PASS')
    print('9/9 Native UI steps; Mock HTTP 1; real provider requests 0')
    print('Receipt: ' + str((OUT / 'ui-preparer-receipt.json').relative_to(ROOT)))
