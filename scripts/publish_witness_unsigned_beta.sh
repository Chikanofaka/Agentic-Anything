#!/usr/bin/env bash
# Publish the existing macOS arm64 portable build as an explicitly UNSIGNED GitHub prerelease.
# This does NOT use Apple Developer ID, notarytool, or Apple credentials.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
REPO="Chikanofaka/HAL-P2D-001"
BRANCH="fix/wtl029-adhoc-bundle-signature"
TAG="v0.3.0-beta.2-adhoc"
APP="$ROOT/integrations/witness_loop/dist/Witness Loop Portable.app"
OUT_DIR="$ROOT/integrations/witness_loop/dist/unsigned-release"
ZIP="$OUT_DIR/WitnessLoop-v0.3.0-beta.2-adhoc-macOS-arm64.zip"
SHA="$ZIP.sha256"
NOTES="$ROOT/packaging/RELEASE_NOTES_v0.3.0-beta.2-adhoc.md"

[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || { echo "MACOS_ARM64_REQUIRED"; exit 2; }
[[ "$(git branch --show-current)" == "$BRANCH" ]] || { echo "WRONG_GIT_BRANCH: switch to $BRANCH"; exit 2; }
[[ "${WITNESS_RIGHTS_APPROVED:-}" == "YES" ]] || { echo "RIGHTS_GATE: Set WITNESS_RIGHTS_APPROVED=YES only after reviewing rights to distribute all included code and artwork."; exit 2; }
[[ -d "$APP" && -x "$APP/Contents/MacOS/WitnessLoop" && -x "$APP/Contents/Helpers/WitnessCore/WitnessCore" ]] || { echo "PORTABLE_BUILD_MISSING: build the portable App first"; exit 2; }
[[ -f "$NOTES" ]] || { echo "RELEASE_NOTES_MISSING"; exit 2; }
[[ "$(/usr/libexec/PlistBuddy -c 'Print :WitnessDevelopmentBuild' "$APP/Contents/Info.plist")" == "false" ]] || { echo "DEVELOPMENT_BUNDLE_REFUSED"; exit 2; }
[[ -f "$APP/Contents/Resources/WitnessLoop.icns" ]] || { echo "APP_ICON_MISSING"; exit 2; }
# The downloaded Beta 1 failed signature verification; never republish without a valid resource seal.
codesign --verify --deep --strict --verbose=4 "$APP" || { echo "INVALID_APP_SIGNATURE: rebuild with updated script first"; exit 2; }
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
ditto "$APP" "$STAGING/Witness Loop.app"
(
  cd "$STAGING"
  ditto -c -k --sequesterRsrc --keepParent "Witness Loop.app" "$ZIP"
)
unzip -tq "$ZIP" >/dev/null || { echo "ZIP_INTEGRITY_FAILED"; exit 3; }
(
  cd "$OUT_DIR"
  shasum -a 256 "$(basename "$ZIP")" > "$(basename "$SHA")"
)
echo "PACKAGED_UNSIGNED_BETA: $ZIP"
echo "NO_APPLE_SIGNING_OR_NOTARIZATION: the beta may be blocked by Gatekeeper."
# This line is the only external publication action.
gh release create "$TAG" "$ZIP" "$SHA" \
  --repo "$REPO" \
  --target "$BRANCH" \
  --title "Witness Loop v0.3.0 Beta 2 — AD-HOC SIGNED (Apple Silicon)" \
  --notes-file "$NOTES" \
  --prerelease
echo "RELEASE_URL:"
gh release view "$TAG" --repo "$REPO" --json url --jq '.url'
