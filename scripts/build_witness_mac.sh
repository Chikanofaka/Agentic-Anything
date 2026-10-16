#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop.app"
CACHE="$ROOT/integrations/witness_loop/.build-cache"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources" "$CACHE"
/usr/bin/swiftc -target "$(uname -m)-apple-macosx12.0" -swift-version 5 -module-cache-path "$CACHE" \
  "$ROOT/integrations/witness_loop/native/OpenAI.swift" \
  "$ROOT/integrations/witness_loop/native/StrictJSON.swift" \
  "$ROOT/integrations/witness_loop/native/Worker.swift" \
  "$ROOT/integrations/witness_loop/native/SelfTests.swift" \
  "$ROOT/integrations/witness_loop/native/UISmoke.swift" \
  "$ROOT/integrations/witness_loop/native/main.swift" \
  -framework AppKit -framework WebKit -o "$APP/Contents/MacOS/WitnessLoop"
/usr/bin/python3 - "$ROOT" "$APP" <<'PY'
import json
import pathlib
import plistlib
import shutil
import sys
root, app = map(pathlib.Path, sys.argv[1:])
resources = app / 'Contents' / 'Resources'
for source, target in [(root / 'runtime' / 'hal_core', resources / 'runtime' / 'hal_core'),
                       (root / 'runtime' / 'trusted_adapters', resources / 'runtime' / 'trusted_adapters'),
                       (root / 'runtime' / 'fixtures', resources / 'runtime' / 'fixtures'),
                       (root / 'integrations' / 'witness_loop' / 'ui', resources / 'ui')]:
    if source.exists():
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
(resources / 'config.json').write_text(json.dumps({'project_root': str(root)}), encoding='utf-8')
info = {'CFBundleName': 'Witness Loop', 'CFBundleDisplayName': 'Witness Loop · HAL',
        'CFBundleIdentifier': 'local.hal.witness-loop', 'CFBundleExecutable': 'WitnessLoop',
        'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '1', 'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0', 'NSPrincipalClass': 'NSApplication',
        'NSAppTransportSecurity': {'NSAllowsArbitraryLoads': False}}
with (app / 'Contents' / 'Info.plist').open('wb') as handle:
    plistlib.dump(info, handle)
PY
"$APP/Contents/MacOS/WitnessLoop" --self-test
printf 'Built local unsigned prototype: %s\n' "$APP"
