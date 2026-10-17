#!/usr/bin/env bash
# Explicit release pipeline: Developer ID sign -> notarize -> staple -> DMG -> GitHub prerelease.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
: "${DEVELOPER_ID_APPLICATION:?Set DEVELOPER_ID_APPLICATION to the installed Developer ID Application certificate name}"
: "${NOTARY_KEYCHAIN_PROFILE:?Set NOTARY_KEYCHAIN_PROFILE to an xcrun notarytool stored credential profile}"
VERSION="v0.3.0-beta.1"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop Portable.app"
RELEASE="$ROOT/integrations/witness_loop/dist/release"
SIGNED="$RELEASE/Witness Loop.app"
DMG="$RELEASE/WitnessLoop-v0.3.0-beta.1-macOS-arm64.dmg"
ENTITLEMENTS="$ROOT/packaging/WitnessLoop.DeveloperID.entitlements"
[[ "$(uname -s)" == Darwin ]] || { echo "macOS required"; exit 1; }
[[ -d "$APP" ]] || { echo "Portable app missing. Build first."; exit 1; }
[[ ! -e "$RELEASE" ]] || { echo "Release output exists; archive/remove intentionally before rerun."; exit 1; }
command -v gh >/dev/null || { echo "GitHub CLI gh required"; exit 1; }
gh auth status >/dev/null
git diff --quiet && git diff --cached --quiet || { echo "Dirty tracked working tree"; exit 1; }
[[ "$(git branch --show-current)" == "feat/wtl029-portable-beta" ]] || { echo "Wrong branch"; exit 1; }
[[ -f "$ENTITLEMENTS" ]] || { echo "Entitlements missing"; exit 1; }
security find-identity -v -p codesigning | grep -F "$DEVELOPER_ID_APPLICATION" >/dev/null || { echo "Developer ID Application identity unavailable"; exit 1; }
xcrun notarytool history --keychain-profile "$NOTARY_KEYCHAIN_PROFILE" >/dev/null || { echo "Notary credentials unavailable"; exit 1; }
if gh release view "$VERSION" --repo Chikanofaka/HAL-P2D-001 >/dev/null 2>&1; then
  echo "Release already exists; refusing to overwrite"
  exit 1
fi
mkdir -p "$RELEASE"
ditto "$APP" "$SIGNED"
/usr/libexec/PlistBuddy -c "Print :WitnessDevelopmentBuild" "$SIGNED/Contents/Info.plist" | grep -qx false || { echo "Not a release-mode app"; exit 1; }
[[ -x "$SIGNED/Contents/Helpers/WitnessCore/WitnessCore" ]] || { echo "Bundled Core missing"; exit 1; }
# Sign embedded Mach-O binaries in leaf-first order. Do not use codesign --deep to sign.
while IFS= read -r -d '' binary; do
  if file -b "$binary" | grep -q 'Mach-O'; then
    codesign --force --sign "$DEVELOPER_ID_APPLICATION" --options runtime --timestamp --entitlements "$ENTITLEMENTS" "$binary"
  fi
done < <(find "$SIGNED/Contents/Helpers/WitnessCore" -type f -print0)
codesign --force --sign "$DEVELOPER_ID_APPLICATION" --options runtime --timestamp --entitlements "$ENTITLEMENTS" "$SIGNED/Contents/Helpers/WitnessCore/WitnessCore"
codesign --force --sign "$DEVELOPER_ID_APPLICATION" --options runtime --timestamp --entitlements "$ENTITLEMENTS" "$SIGNED"
codesign --verify --deep --strict --verbose=2 "$SIGNED"
spctl --assess --type execute --verbose=4 "$SIGNED" || echo "Pre-notarization Gatekeeper assessment inconclusive; notarization remains mandatory"
ditto -c -k --keepParent "$SIGNED" "$RELEASE/notary-submission.zip"
xcrun notarytool submit "$RELEASE/notary-submission.zip" --keychain-profile "$NOTARY_KEYCHAIN_PROFILE" --wait
xcrun stapler staple "$SIGNED"
xcrun stapler validate "$SIGNED"
codesign --verify --deep --strict --verbose=2 "$SIGNED"
# Create a user-friendly read-only DMG. The signed and stapled app is inside.
hdiutil create -volname "Witness Loop" -srcfolder "$SIGNED" -ov -format UDZO "$DMG"
# Notarize the final DMG as well; only a successful notarization reaches GitHub.
xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_KEYCHAIN_PROFILE" --wait
xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
spctl --assess --type open --context context:primary-signature -v "$DMG" || { echo "Gatekeeper DMG assessment failed"; exit 1; }
shasum -a 256 "$DMG" > "$DMG.sha256"
# No publication unless signing, notarization and DMG acceptance have all passed.
git fetch origin
git rev-parse HEAD | grep -qx "$(git rev-parse origin/feat/wtl029-portable-beta)" || { echo "Local HEAD differs from remote branch"; exit 1; }
gh release create "$VERSION" "$DMG" "$DMG.sha256" --repo Chikanofaka/HAL-P2D-001 \
  --target feat/wtl029-portable-beta --title "Witness Loop v0.3.0 Beta 1 (macOS Apple Silicon)" \
  --notes-file "$ROOT/packaging/RELEASE_NOTES_v0.3.0-beta.1.md" --prerelease
echo "RELEASE_PUBLISHED: https://github.com/Chikanofaka/HAL-P2D-001/releases/tag/$VERSION"
