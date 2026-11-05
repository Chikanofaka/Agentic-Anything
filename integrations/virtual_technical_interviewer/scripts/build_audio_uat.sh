#!/usr/bin/env bash
set -euo pipefail
TIA_AUDIO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TIA_AUDIO_APP="$TIA_AUDIO_ROOT/dist/TIA Audio Lab.app"
TIA_AUDIO_CACHE="$TIA_AUDIO_ROOT/.build-cache/audio-uat"
# Never replace the interview application or follow generated-output symlinks.
for target in "$TIA_AUDIO_CACHE" "$TIA_AUDIO_APP" "$TIA_AUDIO_APP/Contents" "$TIA_AUDIO_APP/Contents/MacOS" "$TIA_AUDIO_APP/Contents/Resources" "$TIA_AUDIO_APP/Contents/Resources/ui"; do
  cursor="$target"
  while [[ "$cursor" != / ]]; do
    if [[ -L "$cursor" || ( -e "$cursor" && ! -d "$cursor" ) ]]; then
      printf 'Unsafe audio lab directory: %s\n' "$cursor" >&2
      exit 1
    fi
    cursor="$(dirname "$cursor")"
  done
done
mkdir -p "$TIA_AUDIO_CACHE/modules" "$TIA_AUDIO_APP/Contents/MacOS" "$TIA_AUDIO_APP/Contents/Resources/ui"
for target in "$TIA_AUDIO_APP/Contents/MacOS/TIAAudioLab" "$TIA_AUDIO_APP/Contents/Info.plist"; do
  [[ ! -L "$target" ]] || exit 1
done
/usr/bin/swiftc -parse-as-library -target "$(uname -m)-apple-macosx12.0" -swift-version 5 \
  -module-cache-path "$TIA_AUDIO_CACHE/modules" \
  "$TIA_AUDIO_ROOT/native/Voice.swift" "$TIA_AUDIO_ROOT/native/VoiceTests.swift" \
  "$TIA_AUDIO_ROOT/native/AudioUAT.swift" "$TIA_AUDIO_ROOT/native/AudioUATMain.swift" \
  -framework AppKit -framework WebKit -framework AVFoundation -framework Speech \
  -o "$TIA_AUDIO_APP/Contents/MacOS/TIAAudioLab"
for source in audio-uat.html audio-uat.js audio-uat.css voice.js voice.css; do
  [[ ! -L "$TIA_AUDIO_ROOT/ui/$source" && ! -L "$TIA_AUDIO_APP/Contents/Resources/ui/$source" ]] || exit 1
  cp "$TIA_AUDIO_ROOT/ui/$source" "$TIA_AUDIO_APP/Contents/Resources/ui/$source"
done
cat > "$TIA_AUDIO_APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>TIA Audio Lab</string>
<key>CFBundleDisplayName</key><string>TIA Audio Lab</string>
<key>CFBundleIdentifier</key><string>local.hal.tia-audio-lab</string>
<key>CFBundleExecutable</key><string>TIAAudioLab</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
<key>NSPrincipalClass</key><string>NSApplication</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSMicrophoneUsageDescription</key><string>Test local microphone capture and speech detection in the isolated audio lab. Audio is not saved or sent to an AI provider.</string>
<key>NSSpeechRecognitionUsageDescription</key><string>Test on-device transcription only. No cloud speech fallback or AI requests.</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsArbitraryLoads</key><false/></dict>
</dict></plist>
PLIST
"$TIA_AUDIO_APP/Contents/MacOS/TIAAudioLab" --self-test
printf 'Built isolated audio lab: %s\n' "$TIA_AUDIO_APP"
