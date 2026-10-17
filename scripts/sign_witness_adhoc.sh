#!/usr/bin/env bash
# Repair only the repository's freshly assembled portable BUILD OUTPUT.
# This script is not an end-user Gatekeeper workaround and must not be used on
# downloaded applications. Never touches ~/Downloads, /Applications or saves.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop Portable.app"
[[ "$(uname -s)" == "Darwin" ]] || { echo "MACOS_REQUIRED"; exit 2; }
[[ -d "$APP" ]] || { echo "PORTABLE_APP_NOT_FOUND: $APP"; exit 2; }
[[ -x "$APP/Contents/MacOS/WitnessLoop" ]] || { echo "NATIVE_HOST_NOT_FOUND"; exit 2; }
[[ -x "$APP/Contents/Helpers/WitnessCore/WitnessCore" ]] || { echo "PACKAGED_CORE_NOT_FOUND"; exit 2; }
[[ "$(/usr/libexec/PlistBuddy -c 'Print :WitnessDevelopmentBuild' "$APP/Contents/Info.plist")" == "false" ]] || {
  echo "DEVELOPER_BUILD_REFUSED"; exit 2;
}
# macOS signs the full bundle and its resource seal. Finder metadata, resource
# forks and provenance attributes carried through cp -R can make signing fail.
# Clear extended attributes ONLY on this generated, owned build-stage copy.
# This does not bypass the quarantine of apps downloaded from GitHub.
xattr -cr "$APP"
# Ad-hoc-sign the assembled final application after its Info.plist and embedded
# PyInstaller worker are already in place. PyInstaller signs its Mach-O internals.
codesign --force --sign - "$APP"
codesign --verify --deep --strict --verbose=4 "$APP"
echo "PASS FINAL_APP_ADHOC_SIGNATURE: $APP"
echo "NOT_DEVELOPER_ID_NOT_NOTARIZED: downloaded copies can still be blocked by Gatekeeper."
