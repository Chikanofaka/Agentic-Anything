# TIA Audio Lab verification — 2026-11-05

## Scope

This receipt covers the isolated local-audio closed loop only. The laboratory
uses the production native speech backend and voice companion with scripted
local interviewer replies. It does not load the Python worker, OpenAI provider,
API credentials, interview scoring, or question-transition controller.

Source baseline: `d7dfd7c` (`feat/tia-evaluator-agent`).

## Automated acceptance

- Full TIA development App build: PASS.
- Production voice unit tests: 154 passed, 0 failed.
- Audio Lab native tests: 12 passed, 0 failed.
- Audio Lab WebKit synthetic closed loop: 9 checks passed.
- Synthetic microphone captures: 0.
- Synthesized audio during automated tests: 0.
- Provider/model requests: 0.
- Hardware microphone, speech recognition, TTS, TCC prompts, acoustic echo
  behavior, and physical barge-in: `NOT_RUN` until human UAT.

Post-UAT repair synthetic report:

`engineering/audio_uat/verification/audio-fix-20261105/D6A225F0-C804-4F9B-8848-FBF9EB4340EA/report.json`

The same synthetic bridge run created a separate, private export artifact at
`exported-report.json` in that run directory. Both files were verified as
regular files with mode `0600`; the exported artifact records zero provider
requests and `transcript_saved: false`.

The report contains diagnostic metadata, checklist states, and optional human
notes. It contains no transcript, voice draft, interviewer caption, raw audio,
API key, or provider payload.

## Production integration regression

The full App compiled successfully with the Audio Lab changes and its native
test bundle passed. A broader `verify_app.py --ui --voice` run passed Python,
native build, general WebKit, recovery, setup, mocked-live, mocked-live recovery,
and mocked-provider-failure stages. Its pre-existing full rehearsal stage then
timed out at the UI watchdog after six Q1 turns, Q1 Final Submit, and Q2 Skip.
Because the command exited nonzero before reaching its voice stage, it is not
reported as a complete pass and remains a separate integration regression.

## Human hardware UAT

From the repository root, run:

```bash
/bin/bash integrations/virtual_technical_interviewer/scripts/run_audio_uat.sh
```

The App displays the exact state transition, native diagnostic timeline,
signal ladder, scripted local conversation, and an 18-item acceptance checklist.
Complete the permission, transcription, five-second seal, exactly-once,
barge-in, echo rejection, manual input, pause, mute/replay, language, drag,
focus, recovery, export, and stop-isolation checks. Review free-text notes before
sharing `report.json`; the file is private (`0600`) and intentionally omits
audio and transcript content.

## Real UAT failure and repair

The first hardware UAT proved that permissions, the audio engine, physical
microphone frames, and candidate-speech activity were operational. Its native
timeline repeatedly showed `AUDIO_INPUT_CONFIGURED` with nine source channels,
followed by candidate RMS/activity but no `RECOGNIZER_RESULT`, ending in
`VOICE_RECOGNITION_STALLED`. The recognizer had been receiving the aggregate
nine-channel Voice Processing buffer directly.

The repaired backend now converts that aggregate input to non-interleaved mono
Float32 before it reaches both the recognizer and candidate detector. It maps
only channel zero—the post-echo-cancellation microphone channel already proven
to contain candidate speech—so output/reference channels are not mixed back
into recognition. Automated coverage confirms multi-channel conversion,
channel selection, five-second sealing, exactly-once delivery, barge-in, stale
callback rejection, and failure fallback. A second human hardware run remains
required to certify actual Apple Speech transcription on this Mac.

The original Export action only refreshed the internal per-run report. Export
now opens a non-blocking native Save panel, writes a distinct JSON artifact with
mode `0600`, reports the exact selected path in the UI, and reveals the file in
Finder. The Save panel is allowed up to ten minutes and therefore cannot trip
the ordinary 15-second bridge timeout. Synthetic automation uses an injected
destination and never opens a dialog.

No API key or paid model authorization is required. If the App reports local
speech unavailable, use its native timeline and signal ladder to identify the
failed stage rather than testing through the real interview.
