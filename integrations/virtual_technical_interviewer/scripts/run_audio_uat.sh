#!/usr/bin/env bash
set -euo pipefail
TIA_AUDIO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TIA_AUDIO_APP="$TIA_AUDIO_ROOT/dist/TIA Audio Lab.app"
TIA_AUDIO_REPORTS="$TIA_AUDIO_ROOT/.build-cache/audio-uat/runs"
case "${1:-}" in
  ""|--build-only|--self-test|--smoke) ;;
  *) printf 'Usage: bash %s [--build-only|--self-test|--smoke]\n' "$0" >&2; exit 2 ;;
esac
/bin/bash "$TIA_AUDIO_ROOT/scripts/build_audio_uat.sh"
case "${1:-}" in
  --build-only|--self-test) exit 0 ;;
  --smoke) exec "$TIA_AUDIO_APP/Contents/MacOS/TIAAudioLab" --smoke --report-root "$TIA_AUDIO_REPORTS" ;;
esac
printf 'Opening REAL local microphone/STT/TTS lab; replies are SCRIPTED. No API key or paid calls.\nReports (metadata and your notes only): %s/<run-id>/report.json\nPress Begin in the lab when ready.\n' "$TIA_AUDIO_REPORTS"
/usr/bin/open -n "$TIA_AUDIO_APP" --args --report-root "$TIA_AUDIO_REPORTS"
