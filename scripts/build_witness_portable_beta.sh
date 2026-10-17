#!/usr/bin/env bash
# Developer preview of a relocatable, unsigned macOS app. No signing or publishing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${WITNESS_PACKAGING_PYTHON:-python3}"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop.app"
CACHE="$ROOT/integrations/witness_loop/.build-cache/portable"
OUTPUT="$ROOT/integrations/witness_loop/dist/Witness Loop Portable.app"

command -v "$PYTHON" >/dev/null || { echo "PACKAGING_PYTHON_NOT_FOUND"; exit 2; }
"$PYTHON" -m PyInstaller --version >/dev/null 2>&1 || {
  echo "PYINSTALLER_REQUIRED: use a separate packaging virtualenv with PyInstaller >= 6. Install deliberately, then set WITNESS_PACKAGING_PYTHON."
  exit 2
}
[[ "$(uname -s)" == "Darwin" ]] || { echo "MACOS_BUILD_ONLY"; exit 2; }

# Rebuild local developer app; do not modify it with signing/package resources.
bash "$ROOT/scripts/build_witness_mac.sh"
mkdir -p "$CACHE"
# Keep builds and spec files outside the source tree.
"$PYTHON" -m PyInstaller --noconfirm --clean --onedir --name WitnessCore \
  --paths "$ROOT/runtime" \
  --collect-submodules hal_core --collect-submodules trusted_adapters \
  --add-data "$ROOT/runtime/fixtures:fixtures" \
  --add-data "$ROOT/runtime/trusted_adapters/witness_character.json:trusted_adapters" \
  --distpath "$CACHE/py-dist" --workpath "$CACHE/py-build" --specpath "$CACHE" \
  "$ROOT/scripts/witness_core_entry.py"

CORE="$CACHE/py-dist/WitnessCore/WitnessCore"
[[ -x "$CORE" ]] || { echo "PACKAGED_CORE_MISSING"; exit 3; }
[[ ! -e "$OUTPUT" ]] || { echo "OUTPUT_ALREADY_EXISTS: move or remove the old portable test app intentionally"; exit 3; }
cp -R "$APP" "$OUTPUT"
mkdir -p "$OUTPUT/Contents/Helpers/WitnessCore"
cp -R "$CACHE/py-dist/WitnessCore/." "$OUTPUT/Contents/Helpers/WitnessCore/"
/usr/libexec/PlistBuddy -c "Set :WitnessDevelopmentBuild false" "$OUTPUT/Contents/Info.plist"
# swiftc/ld and PyInstaller can ad-hoc sign individual Mach-O executables during build.
# Assembling runtime files and editing Info.plist AFTER that invalidates/omits the
# *outer app resource seal*. Sign the complete, final app bundle inside-out (the
# PyInstaller nested Mach-O code is already signed), then verify before shipping.
# Ad-hoc (-) does NOT make Gatekeeper treat the app as Developer ID/notarized.
codesign --force --sign - "$OUTPUT"
codesign --verify --deep --strict --verbose=2 "$OUTPUT" || {
  echo "PORTABLE_SIGNATURE_INVALID: do not distribute this app"
  exit 3
}
# Exercise the embedded executable with an isolated synthetic storage directory.
SMOKE="$CACHE/portable-smoke-$(date +%s)-$$"
mkdir -p "$SMOKE"
printf '%s\n' '{"id":"portable-1","action":"snapshot","params":{}}' | \
  "$OUTPUT/Contents/Helpers/WitnessCore/WitnessCore" --data-dir "$SMOKE" > "$SMOKE/output.json"
"$PYTHON" - "$SMOKE/output.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    obj = json.loads(f.readline())
assert obj['id'] == 'portable-1' and obj['ok'] is True, obj
assert obj['result']['state']['schema'] == 'witness-state/v2', obj
print('PASS embedded Core initial snapshot; synthetic save only')
PY
echo "UNSIGNED_PORTABLE_PREVIEW_BUILT: $OUTPUT"
echo "ADHOC_SIGNED_NOT_NOTARIZED_NOT_RELEASED; ad-hoc signature integrity passed, Gatekeeper may still reject the download."
