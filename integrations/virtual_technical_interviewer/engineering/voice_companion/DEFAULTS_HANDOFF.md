# Automatic voice entry defaults — 2026-10-24

Owner request supersedes the initial manual-mode default documented in HANDOFF.md. Each fresh verified question now starts with the companion minimized, automatic sending selected, and the committed interviewer introduction read aloud before local listening begins. Microphone/Speech permission and device-only support remain required. Pause and manual mode persist through snapshots and replies in the current question; the next fresh question resets the defaults. Previously entered/reconnected questions and recovered conversations containing candidate evidence do not silently restart recording.

The extra hands-free confirmation sheet is removed. Native provider authorization now explains automatic voice turns within the existing request cap; no additional spending authority is introduced. Switching off automatic sending retains editable drafts. Native credential sheets, focus loss, disconnect and failures still stop capture. Audio remains local; transcribed text follows the existing model transaction.

Changed source: `native/Voice.swift`, `native/main.swift`, `ui/voice.js`, `native/VoiceTests.swift`, `native/VoiceUISmoke.swift`; updated usage in README.md. The original manual-mode regression journey now explicitly selects manual mode. Six added native checks cover initial playback/listening, automatic submission, pause persistence, new-question reset and permission failure. WebKit tests assert minimized entry, checked automatic sending and active synthetic listening.

Verification command:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3D --ui --regressions --voice --run-label local-voice-defaults-20261024-01
```

[Final receipt](verification/local-voice-defaults-20261024-01/receipt.json): 16 groups PASSED, 0 FAILED, 0 SKIPPED. 498 Python tests; 133 native checks; 69 provider checks; 100 voice checks; 122 WebKit/native/controller checks (24 voice); Witness 52 native and HAL 287 Python regression checks passed. Source hashes matched after verification. No real audio capture, real credential or paid API call was used. Device UAT of these new defaults remains NOT_RUN.

Build and open from the isolated voice checkout:

```sh
bash integrations/virtual_technical_interviewer/scripts/build_app.sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

Checkout: `~/Developer/Agentic-Anything-tia-voice`, branch `feat/tia-voice-companion`. No push or merge into the active development branch. Next: test a fresh question on-device, confirm automatic reply/listening and compact controls, then pause or select manual mode; confirm the next fresh question resets defaults.
