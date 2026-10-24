#!/usr/bin/env bash
set -euo pipefail
TIA_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="$TIA_ROOT/.build-cache"
APP="$TIA_ROOT/dist/Technical Interview Lab.app"
/usr/bin/python3 "$TIA_ROOT/scripts/check_build_paths.py"
mkdir -p "$CACHE" "$APP/Contents/MacOS"
/usr/bin/swiftc -target "$(uname -m)-apple-macosx12.0" -swift-version 5 \
  -module-cache-path "$CACHE" \
  "$TIA_ROOT/native/Bridge.swift" "$TIA_ROOT/native/Worker.swift" \
  "$TIA_ROOT/native/OpenAI.swift" "$TIA_ROOT/native/NativePreparer.swift" "$TIA_ROOT/native/StrictJSON.swift" \
  "$TIA_ROOT/native/NativeProvider.swift" "$TIA_ROOT/native/ProviderTests.swift" \
  "$TIA_ROOT/native/Voice.swift" "$TIA_ROOT/native/VoiceTests.swift" "$TIA_ROOT/native/VoiceUISmoke.swift" \
  "$TIA_ROOT/native/SelfTests.swift" "$TIA_ROOT/native/UISmoke.swift" "$TIA_ROOT/native/main.swift" \
  -framework AppKit -framework WebKit -framework AVFoundation -framework Speech -o "$APP/Contents/MacOS/TechnicalInterviewLab"
/usr/bin/python3 "$TIA_ROOT/scripts/package_app.py" "$APP"
"$APP/Contents/MacOS/TechnicalInterviewLab" --self-test
printf 'Built local development App: %s\n' "$APP"
