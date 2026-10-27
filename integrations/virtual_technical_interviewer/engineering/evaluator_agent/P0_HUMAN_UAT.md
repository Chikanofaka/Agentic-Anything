# Final P0: Human UAT and implementation boundaries

Prepared 2026-10-27 for the local `feat/tia-evaluator-agent` worktree.

**Human UAT: NOT_RUN. Real acoustic acceptance: NOT_RUN. Integrated live-model acceptance: NOT_RUN.** This checklist is not a completion receipt. No paid model test is authorized to the engineering agents. Mock HTTP, synthetic speech, native/WebKit automation and real temporary PostgreSQL tests establish only their recorded checks; none proves live dialogue quality or speaker-to-microphone echo rejection.

## Before the owner starts

- Record the App build/source identity, dirty-patch identity, macOS version, speech language and audio route. Use the App built from this worktree, not an older installed copy. See [the operating guide](README.md) for build/open commands.
- Preserve existing sessions and exports. Use a separate UAT session with three owner-approved, non-sensitive PostgreSQL questions. Do not reset or rewrite a historical session to test the new policy.
- The human owner must explicitly choose and record the model and maximum paid request count in the **native API Portal**, then consent there. Available caps are 1, 2, 5, 10 and 20 per activation. A cap limits requests, not currency. This document grants no consent. Reconnection requires a fresh human decision; never reconnect automatically to bypass an exhausted cap.
- Budget for private preparation, each opening/verification, each submitted candidate turn, and each requested evaluation. Keep the actual attempt count, including cancelled or invalid attempts; do not infer it from successful dialogue count. Pause the microphone while arranging the test. Audio remains local, but submitted text is sent to the approved provider.
- Prepare independently reviewed fixture JSON for each question, following [the existing fixture validator](../../tia_runtime/sql_accuracy.py). Include meaningful edge cases and independently established expected rows. A model's proposed answer must not be the sole source of the expected result. The fixture must carry the exact question SHA displayed by the App.

## One integrated three-question journey

Record PASS, FAIL or NOT_OBSERVED for each numbered check, with a timestamp and sanitized evidence reference. Any failure keeps the integrated acceptance open.

1. **Activation and private preparation.** Enter the key only in the native secure sheet. Merely storing it remains unverified. After the separate native preparation confirmation, prepare references for all three confirmed questions. Initially they are unverified proposals. For each question, use **Verify Qn reference · local tests**, select its independently reviewed fixture, check the displayed digest and approve native local execution. Confirm three separate question-bound results. A verified label requires actual passing local execution; missing PostgreSQL, unsupported environments, invalid fixtures or failed approaches must remain unverified. Record passed/tested/total approaches and fixture/question hashes. Verification itself must add **zero model requests**. No reference code, rationale or fixture rows may appear in the interview UI or exported receipt.

2. **Room entry and permissions.** Enter a fresh question using `tia-continuity/v3`; preserve old sessions' recorded policy. A successful authorized model response establishes verified access. Check the interviewer opening, minimized voice companion, **Faster** speed and automatic sending enabled. Exercise first-use microphone/speech permission sheets on a suitable test account if available. Granting permissions must not silently clear automatic sending. Denial must show a truthful unavailable/paused state and must not send anything. Pause/Listen and mute must remain usable; pausing the mic must not pause the Host clock.

3. **Five-second silence.** Say a short clause, pause for about two seconds, continue speaking, then stop. Repeat with a four-second pause. No candidate turn or paid request may be created during either pause; resumed acoustic speech restarts the countdown. After at least five uninterrupted seconds of actual silence, a nonempty transcript is delivered exactly once. Check the candidate event and request-count delta, not just the voice animation. Silence/empty recognition alone must send nothing. Early recognizer finalization is not observable in every manual run: record it as NOT_OBSERVED unless independently evidenced; use the automated early-final regression for deterministic coverage, without presenting that as hardware acceptance.

4. **Barge-in and introduction shortcut.** With microphone permission already granted, interrupt interviewer playback with real speech. Playback must stop or duck promptly, retain the beginning of the candidate utterance, and apply the same five-second silence rule. Say “skip the introduction and read the question”: it is a conversation request and must leave the current question index unchanged. Test both headphones and built-in speakers; interviewer playback alone, typing and ordinary room noise must not create candidate turns or consume requests. Record audio route, echo false positives and missed onsets. If echo-resistant monitoring is unavailable, record the limitation rather than marking barge-in passed.

5. **Conversation continuity and Final Submit — Q1.** Complete at least **six candidate/interviewer exchanges** within the 900-second window, including clarification, planning, implementation and a later clarification. Crossing the former fourth-turn boundary must not advance, close or refuse the question. Sending SQL alone must not advance it. Once implementation evidence exists, a later conversational turn must not prevent explicit **Final Submit**. Final Submit closes Q1 once. Confirm the next question receives its own 900-second window when presented. Record actual candidate/reply counts and the closure reason.

6. **Manual Skip — Q2.** Have a real exchange, then use the explicit **Skip Question** control. It advances exactly once and records the skipped outcome. Spoken requests about skipping an introduction must not trigger this control. Request failure, exhausted native budget or cancellation must leave an active question available for recovery, Final Submit or Skip; they must not themselves close it. If a failure is not encountered in this run, mark that manual subcheck NOT_OBSERVED and cite its separate mocked regression.

7. **Host timeout — Q3.** Present the question and allow its full **900 seconds** to elapse without Final Submit or Skip. Use a stopwatch alongside the Host display; do not alter the system clock or inject browser timestamps. Paused microphone and model waiting do not stop elapsed interview time. Host timeout closes the question once, and late replies cannot add a turn or reopen it. Confirm the session has three closed questions with distinct submitted/skipped/timed-out outcomes. Question completion is not evidence of SQL correctness.

8. **Evidence-grounded evaluation.** On the completion page, request evaluation only through each separate native consent and the remaining approved budget. Use questions with candidate evidence; abstention on an evidence-empty skipped question is expected. Compare the entire chronological record, including early and late turns and interviewer feedback, with the evaluator citations. Preserve all **11 criteria: T01–T05 and C01–C06**. Check that cited events belong to the selected frozen question and that absent evidence remains `NOT_OBSERVED`. A local SQL verdict must match the exact submitted SQL and reviewed fixture; private-reference verification does not itself grade candidate SQL. Final Submit is not proof of closing-speech quality. A context-capacity error must be explicit, never replaced by a silently shortened conversation.

9. **Arithmetic and truthful counts.** Check each proposed observed point value using `criterion maximum × anchor / 4`. Technical maxima are 24/13/10/9/4; Communication maxima are 6/7/7/9/7/4. Keep separate observed-point totals, covered weights and missing criteria. Do not normalize missing criteria, convert them to zero, or create a combined 60/40 grade. Final Technical, Communication and Overall remain **NOT_SCORED**. Compare actual closed-question count, SQL submission count, verified local results, candidate/reply counts, native request attempts and supplied token usage with their source records. `LIVE_MODEL`, `SIMULATED` and `MOCK_HTTP` describe different facts and must not be substituted for one another.

10. **Recovery, cancellation and privacy.** Export through the native Save panel, then disconnect and reopen the App. Existing transcript, frozen evaluator results and historical receipts must remain readable without a model request. Credentials and private in-memory references must be gone; reference verification is not promised to survive restart. In a separate disposable checkpoint, cancel an in-flight operation and confirm no late/duplicate commitment, automatic retry or automatic question advancement. If the native commit was already submitted, the UI must truthfully report that boundary rather than claim rollback. Inspect only sanitized exports: no key, raw audio, private reference answer or private verifier packet. Do not copy personal transcripts, keys or raw UAT logs into Git.

## Implementation boundaries to retain

- Native owns credentials, provider requests, local speech and the private reference seal. A separate one-shot local verifier receives reference code over stdin, runs approved isolated PostgreSQL work, and returns bounded hash/status facts. The regular Python Host, WebKit, process arguments and exports do not receive the reference answer.
- Python Host owns authorization, question transitions, the monotonic/wall-clock accounting and immutable evidence commitments. The model cannot execute SQL, issue transitions, authorize hints or assign final grades. Unlimited conversation means no numerical question-turn cap; provider consent caps, per-request bounds and explicit capacity failures still apply.
- New policy v3 and its complete chronological evaluator context must not rewrite legacy policy behavior or pinned receipts. Legacy replay is a separate regression requirement. Local clock integrity remains uncertified; microphone Pause is not interview Pause.
- The evaluator retains the PRD v3 11-criterion proposal. The 12-criterion 70/20/10 experiment remains separate. Source citations and hashes provide traceability, not proof that a model judgment is correct. Native private-reference status does not manufacture candidate execution evidence.
- No commit, push, public release, formal grading approval or Human UAT completion follows automatically from this checklist.

## Human receipt — fill after execution

| Field | Observed value |
|---|---|
| Human operator / date / App and source identity | NOT_RUN |
| Explicitly approved model / per-activation cap | NOT_AUTHORIZED_BY_THIS_DOCUMENT |
| Question policy / question hashes / fixture hashes | NOT_RUN |
| Native request attempts / successful responses / supplied token usage | NOT_RUN |
| Q1/Q2/Q3 candidate and interviewer counts / closure reasons / elapsed seconds | NOT_RUN |
| Reference approaches passed/tested; candidate SQL verified/passed | NOT_RUN |
| All 11 criteria / missing evidence / arithmetic review | NOT_RUN |
| Headphones / built-in speaker echo and barge-in / silence timing | NOT_RUN |
| Recovery / cancellation / sanitized evidence locations | NOT_RUN |
| Failures, NOT_OBSERVED subchecks and human acceptance decision | **NOT_RUN — acceptance remains open** |
