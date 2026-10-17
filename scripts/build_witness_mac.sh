#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop.app"
CACHE="$ROOT/integrations/witness_loop/.build-cache"
# Reviewed source edits deliberately take effect on the next successful rebuild.
/usr/bin/python3 "$ROOT/scripts/compile_witness_character.py"
/usr/bin/python3 "$ROOT/scripts/compile_witness_character.py" --check
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
import hashlib
import pathlib
import plistlib
import shutil
import sys
import tempfile
root, app = map(pathlib.Path, sys.argv[1:])
resources = app / 'Contents' / 'Resources'
if any(path.is_symlink() for path in (app, app / 'Contents', resources)):
    sys.exit('UNSAFE_GENERATED_BUNDLE_PATH')
# Rebuild the generated resources from an empty staging directory. Removed code
# and artwork cannot linger from an earlier app build. Player data is elsewhere.
staged = pathlib.Path(tempfile.mkdtemp(prefix='bundle-', dir=root / 'integrations/witness_loop/.build-cache'))
for source, target in [(root / 'runtime' / 'hal_core', resources / 'runtime' / 'hal_core'),
                       (root / 'runtime' / 'trusted_adapters', resources / 'runtime' / 'trusted_adapters'),
                       (root / 'runtime' / 'fixtures', resources / 'runtime' / 'fixtures'),
                       (root / 'integrations' / 'witness_loop' / 'ui', resources / 'ui')]:
    if not source.is_dir() or source.is_symlink() or any(path.is_symlink() for path in source.rglob('*')):
        sys.exit('MISSING_OR_UNSAFE_BUNDLE_SOURCE')
    shutil.copytree(source, staged / target.relative_to(resources), ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
compiled = json.loads((staged / 'runtime/trusted_adapters/witness_character.json').read_text())
if any(path.name in ('case_brief.md', 'identity.md', 'memory.md', 'user.md', 'narrator_intro.md') for path in staged.rglob('*')):
    sys.exit('RAW_AUTHORING_SOURCE_IN_BUNDLE')
art = [path for path in (staged / 'ui/assets').rglob('*') if path.is_file()]
if not art:
    sys.exit('BUNDLED_ARTWORK_MISSING')
(staged / 'config.json').write_text(json.dumps({'project_root': str(root), 'version': '0.3.0', 'character_digest': compiled['digest']}), encoding='utf-8')
manifest = {'version': '0.3.0', 'character_context': {'version': compiled['version'], 'digest': compiled['digest']},
            'artwork': {str(path.relative_to(staged)): hashlib.sha256(path.read_bytes()).hexdigest() for path in art},
            'raw_authoring_sources_bundled': False, 'live_api_tested': False}
(staged / 'build-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
shutil.rmtree(resources)
staged.rename(resources)
icon_path = root / 'branding' / 'WitnessLoop.icns'
if not icon_path.is_file() or icon_path.is_symlink():
    sys.exit('BRAND_ICON_MISSING')
shutil.copy2(icon_path, resources / 'WitnessLoop.icns')
info = {'CFBundleName': 'Witness Loop', 'CFBundleDisplayName': 'Witness Loop · HAL',
        'CFBundleIdentifier': 'local.hal.witness-loop', 'CFBundleExecutable': 'WitnessLoop', 'CFBundleIconFile': 'WitnessLoop',
        'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '0.3.0',
        'CFBundleVersion': '3', 'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0', 'NSPrincipalClass': 'NSApplication',
        'NSAppTransportSecurity': {'NSAllowsArbitraryLoads': False}}
with (app / 'Contents' / 'Info.plist').open('wb') as handle:
    plistlib.dump(info, handle)
PY
"$APP/Contents/MacOS/WitnessLoop" --self-test
printf 'Built local unsigned prototype: %s\n' "$APP"
