#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Workspace: $ROOT"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 not found: install Python 3.10+ or ask Codex for a local setup plan.' >&2
  exit 127
fi
python3 --version
cd "$ROOT/runtime"
python3 -m unittest discover -s tests -v
python3 -m hal_core.cli inspect --package fixtures/research > /dev/null
python3 -m hal_core.cli inspect --package fixtures/returns > /dev/null
python3 -m hal_core.cli run --package fixtures/research --feature calculate-margin --payload '{"revenue":1500,"cost":900}'
python3 -m hal_core.cli run --package fixtures/returns --feature triage-return --payload '{"condition":"sealed","proof":"yes","days":5}'
echo 'NOTE: ai-interpretation/manus preflight BLOCKED is the expected fail-closed behavior.'
echo 'DONE: offline local verification complete; no model API calls were attempted.'
