#!/usr/bin/env bash
# Final player-facing GitHub metadata sync. Does not rebuild or replace ZIP assets.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OLD="Chikanofaka/HAL-P2D-001"
NEW="Chikanofaka/Witness-Loop"
TAG="v0.3.0-beta.3-adhoc"
NOTES="packaging/RELEASE_NOTES_v0.3.0-beta.3-adhoc.md"
[[ "$(git branch --show-current)" == "main" ]] || { echo "SWITCH_TO_MAIN_FIRST"; exit 2; }
[[ -z "$(git status --porcelain)" ]] || { echo "UNCOMMITTED_WORK: do not auto-add or discard anything"; exit 2; }
gh auth status >/dev/null
git fetch origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo "PULL_MAIN_FIRST"; exit 2; }
[[ -f "$NOTES" ]] || { echo "RELEASE_NOTES_MISSING"; exit 2; }
if gh repo view "$NEW" >/dev/null 2>&1; then
  echo "DESTINATION_NAME_ALREADY_TAKEN_OR_REPO_VISIBLE: inspect manually before renaming"
  exit 2
fi
# Repo rename is a user-authorized, public-facing metadata change.
gh api --method PATCH "repos/$OLD" -f name="Witness-Loop" \
  -f description="雨夜回环 · After the Last Train — an atmospheric detective game for Mac." >/dev/null
# GitHub redirects the old URL; point this local clone explicitly at the new one.
git remote set-url origin "https://github.com/$NEW.git"
gh release edit "$TAG" --repo "$NEW" \
  --title "雨夜回环 · Witness Loop — After the Last Train | Mac Preview" \
  --notes-file "$NOTES"
echo "VERIFY RELEASE AND REPOSITORY"
gh repo view "$NEW" --json nameWithOwner,url,description \
  --jq '{repository:.nameWithOwner,url:.url,description:.description}'
gh release view "$TAG" --repo "$NEW" --json name,url,assets \
  --jq '{title:.name,url:.url,assets:[.assets[].name]}'
echo "SUCCESS: Player-facing repo metadata and published release copy updated."
