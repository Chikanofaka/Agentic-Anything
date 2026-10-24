# Permission-popup recovery — 2026-10-24

User UAT reported Speech/microphone permission dialogs interrupting automatic voice and unchecking automatic sending. Code inspection found that the authorization callback rejected an inactive App before macOS restored focus, and generic pause/error cleanup reset the automatic-sending preference.

The native audio backend now defers authorized capture until App activation, using a cancellable activation gate and the existing generation token. Pause, disconnect and room closure cancel deferred starts. The App uses the actual pending-permission flag instead of the presentation status when handling focus loss.

Automatic sending is now a preference independent of active capture. Pause, credential dialogs, recognition/provider failures, empty utterances and other interruptions stop recording without silently unchecking the setting. No paid retry is introduced. Manual mode remains available through the checkbox; only an explicit toggle or fresh-question defaults change the preference. Permission-denied and other failures remain visible and require explicit recovery; arbitrary backgrounding does not automatically restart capture. Successful macOS permission grants resume the pending listening flow when the App returns to the foreground. Faster (1.2×) and compact entry defaults are unchanged.

Changed source: native/Voice.swift, native/main.swift, native/VoiceTests.swift, native/VoiceUISmoke.swift. README updated. Eight new checks cover deferred foreground activation, exactly-once start, cancellation, pending permissions and preference preservation; UI regression now explicitly selects manual mode and verifies the automatic preference survives credential interruption/disconnect while audio is stopped.

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3D --ui --regressions --voice --run-label local-voice-permissions-20261024-01
```

[Final receipt](verification/local-voice-permissions-20261024-01/receipt.json): 16 groups passed, 0 failed, 0 skipped. TIA Python 498; native 133; provider 69; voice 108; UI 122 (including 24 voice); Witness native 52; shared HAL 287. All recorded source hashes matched after the run. App rebuilt. No real microphone, real credentials or paid calls were used. Actual OS permission-dialog/hardware UAT remains NOT_RUN for this fix.

Quit the running build and reopen `integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app` from the voice checkout. Retest initial permission grants: the automatic checkbox should stay selected, then the mic should listen once the App becomes active. Denial or explicit Pause must stop capture without changing the checkbox. A later Listen resumes the selected mode. No push or merge performed.
