#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
bash "$ROOT/scripts/verify_local.sh"
bash "$ROOT/scripts/build_witness_mac.sh"
echo 'VERIFIED: Core regressions and native mock-provider checks. No live inference. GUI integration is a separate opt-in command.'
