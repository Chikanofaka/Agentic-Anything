#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Workspace: $ROOT"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 not found; no installation attempted.' >&2
  exit 127
fi
python3 --version
cd "$ROOT/runtime"
python3 -B - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit('Python 3.9+ required by current implementation; 3.10+ recommended.')
if sys.version_info < (3, 10):
    print('NOTE: running on Python <3.10; record observed compatibility, not a 3.10+ support-matrix claim.')
PY
python3 -B -m unittest discover -s tests -v
python3 -B - <<'PY'
import json
import subprocess
import sys


def check(arguments, expected_exit):
    completed = subprocess.run([sys.executable, '-B', '-m', 'hal_core.cli'] + arguments,
                               text=True, capture_output=True, check=False)
    if completed.returncode != expected_exit:
        raise SystemExit('CLI verification failed: unexpected exit code')
    output = json.loads(completed.stdout)
    if completed.stderr:
        raise SystemExit('CLI verification failed: unexpected stderr')
    return output


for domain in ('research', 'returns'):
    inspected = check(['inspect', '--package', 'fixtures/' + domain], 0)
    assert inspected['normalized_schema_version'] == 'hal-domain/v1'
    assert inspected['publisher_verified'] is False

research = check(['run', '--package', 'fixtures/research', '--feature', 'calculate-margin',
                  '--payload', '{"revenue":1500,"cost":900}'], 0)
returns = check(['run', '--package', 'fixtures/returns', '--feature', 'triage-return',
                 '--payload', '{"condition":"sealed","proof":"yes","days":5}'], 0)
assert research['result']['profit'] == 600 and research['result']['margin_pct'] == 40
assert returns['result']['classification'] == 'STANDARD_RETURN'
for output in (research, returns):
    assert output['status'] == 'SUCCESS'
    assert output['live_model_used'] is False and output['external_writes'] is False
    print(json.dumps(output, indent=2, sort_keys=True, allow_nan=False))

blocked = check(['preflight', '--package', 'fixtures/research', '--feature',
                 'ai-interpretation', '--provider', 'manus'], 2)
assert blocked['status'] == 'BLOCKED'
assert blocked['missing_ports'] == ['MANAGED_AGENT_PORT_MISMATCH']
assert blocked['live_model_verified'] is False
print(json.dumps(blocked, indent=2, sort_keys=True))
print('VERIFIED: CLI inspection, both domain results, and Manus denial (exit 2).')
PY
echo 'DONE: offline local verification complete; no model API calls were attempted.'
