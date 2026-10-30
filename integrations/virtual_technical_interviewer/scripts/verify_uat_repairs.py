"""Focused offline continuation of the 2026-10-29 UAT repair verification.

Run after verify_app.py --ui --voice --evaluator --post-sql stops at a diagnosed
failure. This does not replace the broad suite; its receipt records that boundary.
All provider transport is mocked. PostgreSQL is an isolated local process.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
repo = root.parents[1]
label = sys.argv[1] if len(sys.argv) == 2 else ''
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', label):
    raise SystemExit('Usage: verify_uat_repairs.py UNIQUE_RUN_LABEL')
out = root / 'engineering/evaluator_agent/verification' / label
out.mkdir(parents=True, exist_ok=False)
cache = root / '.build-cache' / label
app = root / 'dist/Technical Interview Lab.app/Contents/MacOS/TechnicalInterviewLab'
receipt = {'schema': 'tia-uat-repair-continuation/v1', 'checks': [],
           'scope': 'Focused evaluator, post-interview SQL, replay, Witness and HAL; pair with broad verify_app receipt.',
           'real_provider_requests_attempted': 0, 'human_uat': 'NOT_RUN',
           'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'source_parent': subprocess.check_output(['git','rev-parse','HEAD'], cwd=repo, text=True).strip(),
           'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for folder in ('native','ui','tia_runtime','scripts','tests')
               for p in sorted((root/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}}

def run(name, cmd, timeout=240, copied=()):
    start=time.monotonic()
    try:
        result=subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=timeout)
        output=result.stdout+result.stderr; code=result.returncode
    except subprocess.TimeoutExpired:
        output='Verification watchdog expired.'; code=124
    output=output.replace(str(repo), '<repo>').replace(str(Path.home()), '<home>')
    (out/(name+'.txt')).write_text(output)
    receipt['checks'].append({'name': name, 'command': [str(x).replace(str(repo), '<repo>') for x in cmd],
        'exit_code': code, 'elapsed_seconds': round(time.monotonic()-start,3)})
    for source in copied:
        if source.exists(): (out/source.name).write_bytes(source.read_bytes())
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(name, 'PASSED' if code==0 else 'FAILED', flush=True)
    if code:
        print(output[-5000:], flush=True); raise SystemExit(code)

run('python', [sys.executable, '-B', str(root/'run_tests.py')])
run('native-build', ['bash', str(root/'scripts/build_app.sh')])
for name,flag,directory,artifact in (
    ('native-evaluator-webkit','--ui-evaluator-test',cache/'evaluator','ui-evaluator-receipt.json'),
    ('native-evaluator-recovery','--ui-evaluator-recovery-test',cache/'evaluator','ui-evaluator-recovery-receipt.json'),
    ('post-sql-webkit','--ui-post-sql-test',cache/'post-sql','ui-post-sql-receipt.json'),
    ('post-sql-recovery','--ui-post-sql-recovery-test',cache/'post-sql','ui-post-sql-recovery-receipt.json')):
    run(name,[str(app),flag,'--test-output',str(directory)],copied=(directory/artifact,))
run('witness-hal', ['bash',str(repo/'scripts/verify_witness_local.sh')])
receipt['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True))
print('Receipts:',out.relative_to(repo),flush=True)
