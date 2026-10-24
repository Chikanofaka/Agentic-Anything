# Local voice companion v0.1

Owner-approved implementation: local macOS recognition and speech, existing native BYOK interviewer. Isolated branch `feat/tia-voice-companion`, base `e027ae2`. This is an App module, not a separately installed ChatGPT plugin. No shared HAL tool or scoring authority is added.

## Open and use

From this checkout:

```sh
bash integrations/virtual_technical_interviewer/scripts/build_app.sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

In an already verified, active interview room, expand the small floating interviewer icon. Drag its handle, or focus the handle and use arrow keys (Shift for larger moves; Home to reset). Escape collapses the panel. The icon starts compact so the code editor remains accessible.

- **Replay reply** reads the latest committed interviewer response. After you enable local voice, subsequent committed replies are read automatically unless muted. Word highlighting follows the system voice.
- Each fresh verified question opens with the companion minimized, automatic speech sending enabled, and local playback of the introduction followed by listening. macOS Speech and microphone permissions are still required; **Listen** also lets you restart manually. Recognition is device-only. Unsupported devices/languages fail visibly; there is no cloud speech fallback.
- Turn off **Send completed speech automatically** for editable drafts. **Send** submits reviewed text through the existing controller/provider transaction. Clarification, plan/think-aloud, test idea and help are supported. Voice never submits code as an implementation; continue using the existing editor for SQL/Pandas text.
- **Send completed speech automatically** is on for each fresh question, as requested by the owner. The native provider authorization explains this default; no additional per-question confirmation sheet appears. Each completed utterance can consume one previously authorized model request and one existing candidate turn. No paid retry occurs automatically. The panel displays both request and question-turn budgets.
- **Pause mic** stops capture and automatic sending while preserving a review draft and the automatic-sending preference. Press Listen to resume in the selected mode. It does not pause the interview clock or mute playback. **Mute voice** stops playback independently. Listen can interrupt playback; the microphone is suspended while the interviewer speaks or a provider request is pending.
- English/Chinese recognition and installed-system-voice playback are selectable, with 0.8× / 1× / 1.2× rate. Only installed voices are used. No voice assets are downloaded by this feature.

## Contract and privacy

`Voice.swift` supplies a replaceable `TIAVoiceBackend`; `voice.js` exposes `mount`, `update`, and `receive`. The versioned public state is `tia-local-voice/v1`. `BridgePolicy` accepts only exact bounded voice actions. Native Swift owns audio and ephemeral drafts; existing Python preparation, Atlas decisions, transaction commitments and frozen evidence remain unchanged.

No audio file is created. Raw audio never enters WebKit, Python, receipts or model requests. Submitted text enters the existing transcript and authorized provider context. Unsubmitted speech drafts stay in memory; question changes, disconnect, app backgrounding and termination clear native ephemeral voice data. Native credential sheets stop audio and reject attempts to restart it. macOS Speech/microphone permission grants wait for App activation before capture starts; those permission dialogs preserve automatic mode. Other interruptions stop capture without silently changing the selected sending mode. Exports keep the existing controller-only record.

Only committed `LIVE_MODEL` interviewer messages are eligible for speech. Recovered conversations containing candidate events and reconnects to an already entered question do not automatically restart capture or replay history. A fresh question with no candidate events uses the automatic entry defaults. Rejected/cancelled/late model output is not narrated. Spoken requests cannot change the clock, approve hints, disclose reference answers, execute code or assign scores. Existing advisory responses may be narrated; this slice does not introduce an autonomous paid advice scheduler.

Local engineering limits: 1.5 seconds without transcript changes ends an utterance; 45 seconds maximum per utterance; 4096 UTF-8 bytes per draft. These are input bounds, not assessment thresholds. Existing question-turn, request and session-time limits remain authoritative. Device recognition can mishear technical vocabulary: switch to review mode when needed; code entry remains typed.

If a recognition final arrives during a short controller checkpoint, submission may be rejected safely and the draft retained for manual sending. An infrastructure/provider failure stops automatic sending; it never becomes an answer-quality judgment.

## Verification

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py \
  --increment S03-E3D --ui --regressions --voice --run-label your-new-run-label
```

Every automated App invocation uses fail-closed mocked HTTP and synthetic native speech. Neither microphone permissions nor real audio are activated in tests. `--self-test` exercises the same native voice state machine with injected backends. UI checks cross WebKit → Swift → the real Python controller; they include editable drafts, multiple turns, optional automatic sending, retained code-editor text, Chinese settings, native keyboard/mouse interaction and cleanup. The runner also checks the newer adaptive-interviewer/private-preparer paths and existing TIA/Witness/HAL regressions. Results are retained under `verification/`; actual final counts are in `HANDOFF.md`.

## Human device UAT — not yet performed

Use this development App in a separately authorized verified model session; do not place a key in chat or test commands. Any engineer-operated live test requires explicit approval of model and request cap first. A small test can budget three model requests: one verification and two voice turns. No live test has been performed by this work.

1. On fresh verified question entry, check that the panel is minimized and automatic sending is selected. Grant local Speech/microphone permission, check English then Chinese captions and permission-denied recovery. If on-device recognition is unavailable, confirm that the App offers text interaction instead of sending audio elsewhere.
2. Turn automatic sending off, then speak a clarification, pause, correct the transcript and send. Check audible response quality and word highlighting. Confirm no model request before Send in manual mode.
3. Type code while dictating a plan. Confirm editor contents remain intact. Try mute, replay, and interrupting playback with Listen.
4. Exercise default automatic sending, then Pause. Verify that snapshots do not restart it, and that the next fresh question resets the default. Check practical silence timing, background noise and hardware changes. Confirm app backgrounding and credential entry stop capture.
5. Confirm disconnect, question transition and relaunch never restart recording. Compare saved text evidence; Technical and Communication remain governed by the existing unscored/evidence policy.

Physical microphone capture, recognition quality, actual speaker output, audio-device interruptions and paid live conversational latency are **NOT_RUN**. This is an unsigned local development build requiring the same local Python/macOS dependencies as TIA.

Apple platform contracts: [device-only support](https://developer.apple.com/documentation/speech/sfspeechrecognizer/supportsondevicerecognition), [device-only requirement](https://developer.apple.com/documentation/speech/sfspeechrecognitionrequest/requiresondevicerecognition), [Speech permission](https://developer.apple.com/documentation/speech/sfspeechrecognizer/requestauthorization(_:)).
