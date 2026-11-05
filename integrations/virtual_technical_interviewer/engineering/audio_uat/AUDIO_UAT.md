# Isolated audio loop UAT

This lab tests the production local audio component without launching an interview, loading a saved session, opening the API Portal, or constructing a provider. Microphone capture, on-device speech recognition and installed macOS speech synthesis are real in the human test. Interviewer replies are **SCRIPTED**, not AI responses. Passing this lab does not certify SQL, scoring, provider connectivity or full interview UAT.

## Start from Terminal

From this repository root:

```sh
/bin/bash integrations/virtual_technical_interviewer/scripts/run_audio_uat.sh
```

The launcher builds and opens `integrations/virtual_technical_interviewer/dist/TIA Audio Lab.app`. Keep the lab in the foreground and press **Begin**. No API key is needed. On first use, macOS may ask for Speech Recognition and Microphone access. Granting those permissions enables only this local lab. The lab uses the separate bundle identifier `local.hal.tia-audio-lab`; it does not change the main interview app's permission settings.

Use these modes to check software separately from hardware:

```sh
# Compile only.
/bin/bash integrations/virtual_technical_interviewer/scripts/run_audio_uat.sh --build-only

# Native tests with synthetic input: no microphone, speech playback or provider.
/bin/bash integrations/virtual_technical_interviewer/scripts/run_audio_uat.sh --self-test

# WebKit lab test with synthetic speech input/output: no microphone or provider.
/bin/bash integrations/virtual_technical_interviewer/scripts/run_audio_uat.sh --smoke
```

Do not label synthetic checks as a successful real microphone test. Hardware cases below remain **NOT_RUN** until a person performs them on this Mac.

## What should be visible

The floating companion starts minimized. Expand it to see interviewer captions, partial transcription, the editable draft, the automatic-send preference, language and rate. Automatic speech sending and the faster speaking rate are the defaults. The lab page shows diagnostic events and a local turn history; the input/output conversation is held in memory only.

The expected closed loop is:

1. Local permission and recognizer checks succeed.
2. The audio engine starts and PCM input arrives.
3. Candidate activity is detected; partial words become visible.
4. Speech resumes as needed, resetting the silence deadline.
5. At least five uninterrupted seconds after the last detected speech, a nonempty transcript is sealed once.
6. The lab accepts one local turn and presents/reads one scripted reply.
7. Listening resumes for the next candidate turn.

Engine startup, incoming microphone frames, detected speech and recognition text are separate checkpoints. A `LISTENING` label alone does not prove that words are being captured. The diagnostic timeline identifies which checkpoint was reached and the stage/code of a reported failure. It does not contain raw audio or recognized words.

## Human test checklist

Use ordinary test phrases, not passwords, keys or sensitive interview content. Record **Pass**, **Fail**, **Blocked** or **Not run** for every case and add a short note describing the last working step. Keep the lab focused while testing capture, except in the explicit focus-loss case. Related subcases below share one checklist entry; mark that entry Pass only after all applicable subcases pass.

| Case | Action | Expected result |
| --- | --- | --- |
| First-run permissions | Begin with permissions not yet granted; allow both macOS prompts. | Permission stages appear, automatic mode remains selected, and candidate input can start after the prompts. No text is submitted during the prompts. |
| Permission denial | In a separate lab run, deny Speech or Microphone access. | The correct permission failure is shown. No repeated permission loop, no captured/submitted turn, and typed input remains available. Restore access through macOS settings only if you choose to do so; use Listen/Retry explicitly. |
| Ordinary speech | After the introduction, say “I will explain my plan before writing the query.” | PCM/activity and partial text become visible. One local turn is accepted after the silence interval; one scripted response is read. |
| Short pause | Speak a phrase, pause for about two seconds, then continue. | The pause does not send. Both parts remain in the candidate turn. |
| Five-second reset | Speak, pause for about four seconds, then speak again. | The countdown restarts on resumed speech. No submission occurs at the original deadline; one submission follows at least five seconds of new silence. |
| Recognizer segment finalization | Speak several sentences with short pauses for more than one recognizer segment. | A recognizer-final event, if emitted, does not itself send. Segments accumulate until acoustic silence seals the turn. If this device never emits an early final, mark this hardware subcase Not run; the synthetic test covers it deterministically. |
| Exactly once | Complete one phrase and stay silent through the reply and return to listening. | One candidate turn and one scripted reply, with no duplicate caused by a late final or timer. Do not count the next independent utterance as a duplicate. |
| Quiet period | Start listening but do not speak for at least ten seconds. | No empty transcript is sent. Silence alone is not a recognition error. |
| Barge-in | With permissions already granted, use Replay and speak a distinct sentence while the interviewer is reading. | Interviewer audio stops/ducks promptly on candidate onset. The candidate's first words appear, and the five-second rule applies. Test both early and late in playback. |
| Ordinary playback end | Let a reply finish naturally, then speak immediately. | Candidate words arrive after playback; transcription does not remain blocked by the previous playback gate. |
| Echo resistance | With normal speaker volume, let the interviewer read while you remain silent. Repeat with headphones if available. | Interviewer words do not appear as candidate text or create a candidate turn. Record speaker/headphone use and ambient noise in the note. Hardware echo separation is heuristic. |
| Introduction request | Say “Skip the introduction and read the question.” | It remains an ordinary candidate text turn in this scripted lab. It must not invoke a question-skip or navigation command. The scripted reply is not a test of an LLM understanding the instruction. |
| Pause microphone | Start a phrase and click Pause mic before the silence deadline. | Capture stops, no automatic send occurs, and any available partial is preserved for editing. The interview clock is outside this lab. |
| Manual editing | While listening, click Edit draft or focus the draft. Change text and send explicitly. | Listening pauses before editing; typed text stays editable and is not overwritten by a late recognizer callback. Exactly the edited text appears in the in-memory local turn. |
| Automatic preference | Turn automatic send off, speak, and wait five seconds. Then enable it again. | With it off, sealed text waits as a draft. Enabling automatic mode does not silently send that existing draft or start capture; clear/send it and use Listen to start a new turn. |
| Mute and replay | Mute voice, send a typed turn, then unmute and Replay. | Captions still update while muted. Muting playback does not disable candidate text input. Replay does not create another candidate turn. |
| Language and rate | Test English and Chinese separately; try Slower, Normal and Faster. | Selected installed language and speed apply to local audio. A language unavailable for on-device recognition or playback yields a specific failure instead of using cloud audio. Changing settings pauses capture; use Listen again. |
| Focus loss | While listening, switch to another application, then return. | Capture/playback stop and automatic preference remains saved. The lab preserves available words as a paused draft and mutes playback. Listen is required to resume; an inactive window does not silently start capture. Unmute explicitly to restore audible replies. |
| Minimize, expand and drag | Move the companion with its handle, collapse/expand it, and resize the window. Try keyboard focus and movement controls. | Controls remain reachable, the companion stays within the window, and a visual change does not submit a turn or restart the silence interval. |
| Input unavailable and recovery | If input fails or stalls, inspect stage/code, try an explicit Retry, and type a draft. | The failure remains visible, no hidden provider call or paid retry occurs, and manual text remains usable. Record whether PCM, candidate activity and partial text were observed before failure. |
| Stop and restart | Stop the lab during capture, playback and a pending local reply, then Begin again. | Old callbacks cannot append a turn or resume audio after Stop. The next round has a fresh in-memory conversation; the same launch's timeline retains both rounds. Relaunch the app for a separate report directory. |
| Report | Add one test note and export/save the report. Inspect the file before sharing. | The report contains diagnostic metadata, outcomes and the note, with no raw audio, recognized transcript, API key or existing interview session. |

Run the ordinary closed loop at least three times, once after a natural reply end and once after barge-in. One successful turn cannot establish continuity across recognizer rotation or playback handoff.

## Locate the failure before retrying

| Last observed checkpoint | Likely area to inspect | Useful feedback |
| --- | --- | --- |
| No permission completion | macOS access denied/restricted, or app still inactive after the permission sheet | Permission stage/code; whether the lab was foreground |
| Permission granted, local recognizer unavailable | On-device recognition support, language availability or temporary speech service failure | Selected language and exact error code; do not assume all unavailable errors mean a denied microphone |
| Engine fails to start | Input device/format or voice-processing audio setup | Audio-input/echo-cancellation code and selected device type |
| Engine started, no input frames | Microphone routing or capture delivery | Time since startup; whether any PCM checkpoint appeared |
| Frames arrive, no candidate activity | Input level, noise, detector sensitivity or voice-processing path | Whether a clear phrase was spoken, speaker/headphone setup, and whether the activity indicator changed |
| Activity appears, no partial text | On-device recognition task, language/model or playback handoff | First activity time, recognition/segment events, any timeout/error |
| Partial text appears, no seal | Continuing detected sound or silence-clock behavior | Last activity/seal times; whether background sound continued |
| Sealed text, no accepted local turn | Companion submission state or lab bridge | Seal/submit/rejection event sequence and any pending state |
| Local turn accepted, no audible reply | Installed speech voice, mute state or playback device | Caption updated or not; mute/rate/language and playback event/code |
| Reply ends, next speech has no words | Playback-to-capture handoff or recognizer rotation | Natural end versus barge-in; fresh recognition/PCM/activity events |

These are diagnostic branches, not confirmed root causes. Do not keep retrying the full interview to diagnose an isolated microphone problem.

## Reports and isolation

Reports are created in unique run directories beneath `integrations/virtual_technical_interviewer/.build-cache/audio-uat/runs/`. The page displays the active report path. A report stores bounded diagnostic metadata, case outcomes and user-entered feedback notes; it does not store raw audio or recognized candidate/interviewer transcripts. Feedback notes are free text, so review them before sharing. Files are private local artifacts, excluded from Git by the build-cache ignore rule.

The standalone bundle compiles the shared `Voice.swift` component and the lab host. It does not link the Python interview Worker, native provider, SQL execution or Evaluator. No historical interview session, rubric, API request budget or saved transcript is read or modified. The lab has no live-model approval path, and all replies are labeled scripted. Its separate macOS permission identity means passing permissions here does not prove permissions are granted to the main app.

Send back the report and a short statement of audio device/language used. Mark hardware cases that could not be attempted as Not run. Keep the original report locally; the final interview app still needs a small follow-up UAT with its own permission identity after the audio loop is confirmed.
