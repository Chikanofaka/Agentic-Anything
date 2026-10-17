#!/usr/bin/env bash
# Publish the existing macOS arm64 portable build as an explicitly UNSIGNED GitHub prerelease.
# This does NOT use Apple Developer ID, notarytool, or Apple credentials.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
REPO="Chikanofaka/HAL-P2D-001"
BRANCH="fix/wtl029-webkit-white-window"
TAG="v0.3.0-beta.3-adhoc"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop Portable.app"
OUT_DIR="$ROOT/integrations/witness_loop/dist/unsigned-release"
ZIP="$OUT_DIR/WitnessLoop-v0.3.0-beta.3-adhoc-macOS-arm64.zip"
SHA="$ZIP.sha256"
NOTES="$ROOT/packaging/RELEASE_NOTES_v0.3.0-beta.3-adhoc.md"

[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || { echo "MACOS_ARM64_REQUIRED"; exit 2; }
[[ "$(git branch --show-current)" == "$BRANCH" ]] || { echo "WRONG_GIT_BRANCH: switch to $BRANCH"; exit 2; }
[[ "${WITNESS_RIGHTS_APPROVED:-}" == "YES" ]] || { echo "RIGHTS_GATE: Set WITNESS_RIGHTS_APPROVED=YES only after reviewing rights to distribute all included code and artwork."; exit 2; }
[[ -d "$APP" && -x "$APP/Contents/MacOS/WitnessLoop" && -x "$APP/Contents/Helpers/WitnessCore/WitnessCore" ]] || { echo "PORTABLE_BUILD_MISSING: build the portable App first"; exit 2; }
[[ -f "$NOTES" ]] || { echo "RELEASE_NOTES_MISSING"; exit 2; }
[[ "$(/usr/libexec/PlistBuddy -c 'Print :WitnessDevelopmentBuild' "$APP/Contents/Info.plist")" == "false" ]] || { echo "DEVELOPMENT_BUNDLE_REFUSED"; exit 2; }
[[ -f "$APP/Contents/Resources/WitnessLoop.icns" ]] || { echo "APP_ICON_MISSING"; exit 2; }
# The assembled app may gain com.apple.FinderInfo after its build-time signature
# is validated (e.g. if viewed in Finder). Do not sign or strip metadata from
# the original build output here. Re-seal a clean isolated staging copy below.
if grep -q '"project_root"' "$APP/Contents/Resources/config.json"; then
  echo "ABSOLUTE_PROJECT_ROOT_PRESENT: refusing release"; exit 2
fi

command -v gh >/dev/null || { echo "GITHUB_CLI_REQUIRED: install gh (e.g. brew install gh)"; exit 2; }
gh auth status >/dev/null || { echo "GITHUB_LOGIN_REQUIRED: run gh auth login"; exit 2; }
git diff --quiet && git diff --cached --quiet || { echo "UNCOMMITTED_TRACKED_CHANGES"; exit 2; }
git fetch origin "$BRANCH" --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse "origin/$BRANCH")" ]] || { echo "PULL_LATEST_BRANCH_FIRST"; exit 2; }
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "RELEASE_ALREADY_EXISTS: refusing duplicate or overwrite"; exit 2
fi
[[ ! -e "$ZIP" && ! -e "$SHA" ]] || { echo "ARCHIVE_ALREADY_EXISTS: preserve existing files and resolve manually"; exit 2; }

mkdir -p "$OUT_DIR"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
STAGED_APP="$STAGING/Witness Loop.app"
# ditto normally copies Finder attributes and resource forks. --norsrc avoids
# carrying them into a fresh, non-user-controlled release-stage app copy.
ditto --norsrc "$APP" "$STAGED_APP"
xattr -cr "$STAGED_APP"
# Sign the complete app AFTER copying, then verify this exact candidate.
# Only the staging copy is modified; the build output and player saves are not.
codesign --force --sign - "$STAGED_APP"
codesign --verify --deep --strict --verbose=4 "$STAGED_APP" || {
  echo "STAGED_APP_SIGNATURE_INVALID: refusing publication"; exit 3;
}
[[ -x "$STAGED_APP/Contents/Helpers/WitnessCore/WitnessCore" ]] || {
  echo "STAGED_CORE_MISSING"; exit 3;
}
[[ ! -e "$STAGED_APP/Contents/Helpers/WitnessCore/_internal" ]] || {
  echo "OLD_ONEDIR_LAYOUT_REFUSED"; exit 3;
}
# The previous published beta passed codesign but opened only a white UI window.
# Drive the actual WebKit/native/HAL UI flow before archiving; a build that cannot
# render the case brief must not become a public release.
echo "RUNNING_REAL_NATIVE_UI_SMOKE"
"$STAGED_APP/Contents/MacOS/WitnessLoop" --ui-self-test || {
  echo "NATIVE_UI_SMOKE_FAILED: refusing publication"; exit 3;
}
codesign --verify --deep --strict --verbose=4 "$STAGED_APP" || {
  echo "APP_SIGNATURE_CHANGED_AFTER_UI_SMOKE: refusing publication"; exit 3;
}
# Do not use --sequesterRsrc; no Finder resource-fork AppleDouble payloads
# should be reintroduced by the archiver.
ditto -c -k --norsrc --keepParent "$STAGED_APP" "$ZIP"
unzip -tq "$ZIP" >/dev/null || { echo "ZIP_INTEGRITY_FAILED"; exit 3; }
# Check actual archive roundtrip BEFORE uploading anything to the public.
RESTORED="$STAGING/restored"
mkdir -p "$RESTORED"
ditto -x -k --norsrc "$ZIP" "$RESTORED"
codesign --verify --deep --strict --verbose=4 "$RESTORED/Witness Loop.app" || {
  echo "EXTRACTED_APP_SIGNATURE_INVALID: refusing publication"; exit 3;
}
echo "RUNNING_EXTRACTED_APP_UI_SMOKE"
"$RESTORED/Witness Loop.app/Contents/MacOS/WitnessLoop" --ui-self-test || {
  echo "EXTRACTED_APP_UI_SMOKE_FAILED: refusing publication"; exit 3;
}
codesign --verify --deep --strict --verbose=4 "$RESTORED/Witness Loop.app" || {
  echo "EXTRACTED_POST_UI_SIGNATURE_INVALID: refusing publication"; exit 3;
}
echo "PASS EXTRACTED_APP_NATIVE_UI_SMOKE"
(
  cd "$OUT_DIR"
  shasum -a 256 "$(basename "$ZIP")" > "$(basename "$SHA")"
)
echo "PASS STAGED_AND_EXTRACTED_APP_SIGNATURE"
echo "PACKAGED_BETA3_ADHOC: $ZIP"
echo "NO_DEVELOPER_ID_OR_NOTARIZATION: Gatekeeper may still block untrusted downloads."
# This line is the only external publication action.
gh release create "$TAG" "$ZIP" "$SHA" \
  --repo "$REPO" \
  --target "$BRANCH" \
  --title "Witness Loop v0.3.0 Beta 3 — AD-HOC SIGNED (Apple Silicon)" \
  --notes-file "$NOTES" \
  --prerelease
echo "RELEASE_URL:"
gh release view "$TAG" --repo "$REPO" --json url --jq '.url'
