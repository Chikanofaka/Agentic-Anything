#!/usr/bin/env bash
# Verify an already-built Witness Loop portable macOS app without rebuilding it.
# All changes happen inside a disposable isolated staging folder, never inside
# ~/Downloads, /Applications, or the player's Application Support save directory.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_APP="$ROOT/integrations/witness_loop/dist/Witness Loop Portable.app"
[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || {
  echo "MACOS_ARM64_REQUIRED"; exit 2
}
[[ -x "$SRC_APP/Contents/MacOS/WitnessLoop" ]] || { echo "PORTABLE_NATIVE_APP_MISSING"; exit 2; }
[[ -x "$SRC_APP/Contents/Helpers/WitnessCore/WitnessCore" ]] || { echo "BUNDLED_CORE_MISSING"; exit 2; }
[[ ! -e "$SRC_APP/Contents/Helpers/WitnessCore/_internal" ]] || { echo "LEGACY_ONEDIR_LAYOUT_REFUSED"; exit 2; }
[[ "$(/usr/libexec/PlistBuddy -c 'Print :WitnessDevelopmentBuild' "$SRC_APP/Contents/Info.plist")" == "false" ]] || {
  echo "NOT_PORTABLE_RELEASE_MODE"; exit 2
}
for file in index.html app.js style.css assets/platform_empty.png; do
  [[ -r "$SRC_APP/Contents/Resources/ui/$file" ]] || {
    echo "MISSING_UI_RESOURCE: $file"; exit 2
  }
done

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
CANDIDATE="$STAGING/Witness Loop.app"
# Finder may reattach com.apple.FinderInfo to the app sitting on the Desktop.
# Skip resource-fork metadata, then clear extended attributes on ONLY this
# generated staging copy before signing. Never bypass end-user quarantine.
ditto --norsrc "$SRC_APP" "$CANDIDATE"
xattr -cr "$CANDIDATE"
codesign --force --sign - "$CANDIDATE"
codesign --verify --deep --strict --verbose=4 "$CANDIDATE" || {
  echo "STAGED_CODE_SIGNATURE_FAILED"; exit 3
}
echo "PASS TEMPORARY_CANDIDATE_SIGNATURE"
echo "START NATIVE_UI_SMOKE (offline, isolated synthetic saves, no provider calls)"
"$CANDIDATE/Contents/MacOS/WitnessLoop" --ui-self-test || {
  echo "NATIVE_UI_SMOKE_FAILED: keep PR draft; do not publish"; exit 3
}
echo "PASS NATIVE_UI_SMOKE"
# The UI run must not modify signed app resources or reintroduce FinderInfo.
codesign --verify --deep --strict --verbose=4 "$CANDIDATE" || {
  echo "POST_UI_APP_SIGNATURE_FAILED"; exit 3
}
echo "PASS CANDIDATE_SIGNATURE_AFTER_UI"
echo "READY_FOR_NEXT_GATE: locally staged native UI worked; downloaded Gatekeeper behavior still unverified."
