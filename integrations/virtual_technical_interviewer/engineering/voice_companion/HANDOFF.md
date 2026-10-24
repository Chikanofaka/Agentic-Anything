# Local voice companion — implementation receipt

Completed 2026-10-24 on `feat/tia-voice-companion`, based on `e027ae273bfc77b4946858581e3a18473421be5f`. This isolated checkout preserves the active development branch. The commit containing this receipt is the voice delivery commit; identify it with `git log -1 --format=%H -- engineering/voice_companion/HANDOFF.md` from the project directory.

## Delivered behavior

A verified active interview room now has a compact draggable interviewer companion. It supports local English/Chinese speech recognition, editable captions, local reading of committed interviewer replies with word highlighting, replay, microphone pause, independent output mute, speaking-rate control, and explicitly opted-in automatic turn submission. Keyboard movement and a 720 × 600 window are exercised through actual WebKit/native events.

Audio stays on the device. Only submitted text uses the existing native provider and Python prepare/call/commit flow. No new hint, time, code-execution, grading or score authority is introduced. The code editor remains separate. Credential sheets, question closure, disconnect, app backgrounding and termination stop capture; stale callbacks cannot submit another turn. The original three-question accuracy repair remains in its separate checkout and is not represented as completed by this voice change.

## Changed source files

Paths below are relative to `integrations/virtual_technical_interviewer/`:

| File | Change |
| --- | --- |
| `native/Voice.swift` | Device-only recognition, installed voice playback, bounded state machine and backend protocol |
| `native/VoiceTests.swift` | 94 injected-backend state, permission, callback and authority checks |
| `native/VoiceUISmoke.swift` | 24 real WebKit/native/controller checks with synthetic speech and mocked HTTP |
| `native/Bridge.swift` | Exact bounded voice-command allowlist |
| `native/main.swift` | Native voice lifecycle and existing transaction integration; credential-sheet isolation |
| `ui/voice.js` | Draggable, accessible companion and editable speech draft |
| `ui/voice.css` | Compact responsive panel, focus and reduced-motion styles |
| `ui/app.js` | Mount/update voice module, preserve existing request handling |
| `ui/index.html` | Local voice assets |
| `scripts/build_app.sh` | Voice sources/tests, AVFoundation and Speech frameworks |
| `scripts/package_app.py` | Native microphone and speech permission descriptions |
| `scripts/verify_app.py` | Voice/mock UI regression orchestration and non-overwriting run receipts |

Documentation and sanitized synthetic receipts reside in this `engineering/voice_companion/` directory. No controller, provider transport, scoring policy, shared HAL or Witness source is changed.

## Build and launch

From `/Users/harryhsu/Developer/Agentic-Anything-tia-voice`:

```sh
bash integrations/virtual_technical_interviewer/scripts/build_app.sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

Built App: `/Users/harryhsu/Developer/Agentic-Anything-tia-voice/integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app`.

Verified executable SHA-256: `27b98e474955a28b2aff8fcc4f20cf35cd5929fa9895567055eb148c91d05226`.

## Executed verification

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py \
  --increment S03-E3D --ui --regressions --voice \
  --run-label local-voice-20261024-03
```

[Final receipt](verification/local-voice-20261024-03/receipt.json): **16 check groups passed, 0 failed, 0 skipped**, in 111.544 seconds of wall time. Source hashes still matched after the run.

| Executed suite | Passed | Failed |
| --- | ---: | ---: |
| TIA Python, including existing controller and S02/S03 tests | 498 | 0 |
| Existing native checks | 133 | 0 |
| Native mocked-provider checks | 69 | 0 |
| New native voice checks | 94 | 0 |
| WebKit/native/controller checks across 13 UI receipts | 122 | 0 |
| Of those: new voice UI journey | 24 | 0 |
| Witness native regression | 52 | 0 |
| Shared HAL Python regression | 287 | 0 |

These are suite-specific counts, not an invented quality score. No real provider requests, real credentials, microphone capture, permission prompts or synthesized audio were used by automation.

The [voice journey receipt](verification/local-voice-20261024-03/ui-voice-receipt.json) records four mocked HTTP requests: verification plus three candidate dialogue turns. It covers a three-question configured rehearsal, manual clarification and plan, opted-in automatic help turn, microphone resumption after a model reply, unchanged code draft, Chinese settings, compact-window keyboard/mouse movement, credential-sheet capture rejection, question closure and disconnect. It does not claim three questions were graded by this voice test. Existing adaptive reply guards, stale-response recovery, private preparation, tutorial, setup and grading UI suites also passed.

Earlier runs are retained: `local-voice-20261024-01` passed before subsequent fixes and is superseded. `local-voice-20261024-02` stopped on the native drag check after 17 voice checks; native mouse event timing was corrected. The final run above passed the original drag assertion and all remaining checks.

## Remaining gates and next milestone

Physical microphone recognition, audible playback, permission recovery, audio hardware interruptions and live conversation latency are **NOT_RUN**. Follow [device UAT instructions](README.md#human-device-uat--not-yet-performed) next. Any engineer-operated paid UAT requires separate authorization of the model and request cap; this delivery made zero paid calls.

This first version uses half-duplex audio, 1.5-second speech endpointing, a 45-second utterance bound and a 4096-byte transcript bound. A final transcript arriving during a short controller checkpoint can be retained for manual sending instead of being automatically submitted. Existing model and question-turn caps still apply. No autonomous paid guidance scheduler is added. Voice quality, endpoint timing and technical-vocabulary recognition need human testing before broad use.

The smallest next executable milestone is device UAT of two spoken turns, pause/mute and code-editor coexistence, followed by any necessary audio-device recovery fixes. This is a local development build; no merge into the active development branch, push or public release was performed.
