# TIA S03-E — 3-question, time-sensitive, measurable MVI

Version: working engineering plan, 2026-10-22. The S03-D verified base is GitHub branch `feat/tia-s03d-smart-byoq` at `b186e7ed91b9e827ba4245c35d56a38d931a44f8`. Developer-provided local source archive + one separately verified S03-D WebKit hotfix were used as the source input for the E1 candidate. Revalidate patch applicability on the Mac canonical repository before accepting or publishing.

## Product goal and success criterion

A real candidate chooses three human-reviewed BYOQ questions and completes **one 45-minute rehearsal**, with a bounded, native-key-isolated real Senior Interviewer, multiple turns per question, explicit final/skip transitions, hard clock, a frozen event record, verifiable process metrics, an ungraded code-correctness field, a candid Trainer summary, and a specific next SMART drill.

**MVI != validated technical examination.** `setup_launch` must remain blocked without independently validated execution tests and trusted SQL/Pandas adapters; do not relabel incomplete requirements or fabricate correctness.

## Increment / dependency / gate matrix

| Gate | Scope | Explicit acceptance | Status |
| --- | --- | --- | --- |
| D0 | S03-D human-verified BYOQ+Live BYOK base | Native strict schema, secure portal, import and single-turn preview | Verified in prior user UAT; preserved |
| E1 | Three-question, multi-turn session | Each of 3 confirmed questions independently bound, up to 4 candidate turns/question, host-owned Submit/Skip, archived receipts, recovery, UI navigation; no fake grades | Python 140/140 in isolated environment; macOS native/UI and human UAT pending |
| E2 | Host time and event ledger | 45-minute hard total; positive elapsed clock hidden by default; explicit question start/stop; latency separated; deterministic expiry/recovery, no extra time granted on restart | Not implemented |
| E3a | Deterministic metrics and frozen scorecard | 3/3 completion statuses, event-linked attempts, clarifications, helps, phase/time metrics, code `NOT_VERIFIED`, `NOT_SCORED` where not assessed | Not implemented |
| E3b | Read-only Trainer & SMART next drill | Evidence-only, bounded Trainer text; optional paid model consent; distinct reviewer/host authority; one observable SMART goal | Not implemented |
| E4 | Native/WebKit, safety, 45m human UAT | Offline tests and Mock HTTP PASS, real 3-question human journey, compare SHA, feature push then approved main merge | Pending |

## E1 implementation contract (candidate patch)

- `tia_runtime/rehearsal.py`: immutable question allocation (`3 × BYOQ`, 45-min configuration, distinct confirmed digests); no authority or execution.
- `app_host.py`: separate `rehearsal_start`, `rehearsal_submit`, `rehearsal_skip` commands with host-only state machine. Old `setup_launch` stays disabled. Rehearsal starts from question-source or review, including verified source-declared Medium items for **practice only**, without deleting true difficulty labels. Prior frozen previews are retained.
- Reuse `native_prepare_preview`/`native_commit_preview` and Swift `NativePortal`: zero new credential route, no new endpoint or automatic retry. New per-question Controller is independent, with a unique ID and frozen review.
- 4 candidate turns/question, counting *candidate submissions*, not provider requests. An already recorded candidate action is retried without duplicate evidence. Only current-question history enters the provider request. Old context is dropped before the fixed 16KB bound, never the latest candidate action; full evidence remains private.
- Host truthfulness: outcome `SUBMITTED_UNVERIFIED` only if a candidate `implement` event exists; otherwise `DISCUSSION_ONLY`, `NO_SUBMISSION` or `SKIPPED`. SQL/Pandas remains `NOT_RUN`; scores remain `NOT_SCORED`.
- UI: `Start 3-question AI rehearsal`, response input remains active after a model reply until 4 candidate messages, finish or skip to next; at third question, freeze session and show three outcomes with local Export.
- `native/Bridge.swift` accepts only the three exact new zero-parameter public actions. Private native handshake is **not** exposed.
- Native/WebKit smoke test `--ui-rehearsal-test` uses synthetic secure credential and **only mocked HTTP**.

Known E1 limitations (not disguised as completed): no authoritative 45-minute deadline yet; no per-phase time ledger; no correctness engine; no competence scoring; no independent Trainer; no voice; current import has textual boilerplate. API request cap is per Native activation, maximum 20, **not a dollar cap**. For typical 3 opening requests + 4 candidate turns/question, expected 15 requests before retries. Do not run a paid 45-minute UAT before E2/E3; first run E1's bounded functional UAT.

## E2 implementation plan

1. Introduce an immutable `rehearsal_clock/v1` with host authority: `started_at_utc`, monotonic process anchor, elapsed total, and deadline. The user-facing clock displays elapsed count-up only after clicking a clock icon; 45 minutes is a **hard global cutoff**, 15 min/question is a *soft* pacing guideline, not a forced switch.
2. At question issue, append `question_started`; on host finish/skip/timeout append exactly one `question_ended` with index and event ID. Never infer candidate think-time or speech from missing observations.
3. Track separate provider waiting spans (start/success/failure/cancel) to distinguish wall-clock elapsed from measured model latency. Explicit interaction kind (`clarify`, `plan`, `implement`, `help`) is tagged; phase times are not falsely inferred from text content.
4. Recovery: no new interview time for app closure/restart; wall-time deadline remains effective, and monotonic runtime is used during each process. Treat clock anomaly as a surfaced limitation and fail closed for uncertain deadlines. Clock and save compatibility require versioned replay tests.
5. At or after deadline, reject any new paid request, cancel/ignore a late reply and produce a truthful `TIMEOUT` completion/partial result. Do not retroactively edit prior frozen receipts.

## E3a deterministic scorecard contract

- Calculated exclusively from sealed Host event IDs: `questions_presented`, `questions_finished`, `questions_skipped`, `candidate_turns`, `code_submissions`, `clarifications`, `help_requests`, `question_elapsed_seconds`, `total_elapsed_seconds`, `model_wait_seconds` (where observed), `revisions`, `submitted_first_attempt` (if identifiable).
- Require `observed / unknown / not_assessed` flags on each field; self-marked test success or prose cannot become `SQL_PASSED`.
- `technical_correctness.status=NOT_VERIFIED`, `execution.status=NOT_RUN`, `technical_score.status=NOT_SCORED`, `communication_score.status=NOT_SCORED` without independently approved rubric/test execution.
- Link every count and qualitative observation to stable event IDs; an exported digest detects accidental tampering, not attacker-proof identity.

## E3b Trainer gate

- Host reviews the frozen immutable receipt **before** any Trainer model call; no live-session authority and no answer-bank access. Trainer receives only bounded, permitted evidence and returns a compact coaching response with evidence IDs and one SMART training goal.
- Optional native, explicit paid model authorization and a **separate role-specific structured schema**; no accidental use of interviewer schema. Unavailable or skipped Trainer yields objective scorecard + `TRAINER_NOT_RUN`, not invented model advice.
- Candidate/interviewer evaluation kept separate; any interviewer policy violations flagged with host evidence, no agent self-certification.

## Required local gate before push

From canonical repo on `feat/tia-s03e-e1-three-question-runtime` with prior local verification artifacts left uncommitted and untouched:

```
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E1 --ui --regressions
```

Expected currently: 140 Python tests. The second command **has not been run on macOS here**; it is the user's Mac verification gate. All HTTP in automated UI runs is explicitly mocked; no paid live request permitted.

## Human UAT script after E1 Mac PASS

1. Back up/export previous local preview; avoid `Restart/delete` unless explicitly desired.
2. Enter Real AI -> configure 45-min, BYOQ, Strict/Supportive; import and confirm 3 *distinct* problems. No need to edit original Medium labels for a rehearsal.
3. Click `Start 3-question AI rehearsal` (not `Check launch requirements`). Check Q1 of 3 is bound at API Portal.
4. Explicitly authorize up to 20 **potentially paid** requests; Q1 Verify, two candidate responses, Finish; Q2 Verify or Skip; Q3 Verify and answer, Finish.
5. Check three distinct question texts, original source/difficulties, no cross-question model context, frozen results, and `NOT_RUN`/`NOT_SCORED`; export private receipt.
6. Hold `main` until E2/E3 and the full timed 3-question UAT pass; the E1 patch alone is a testing candidate, not production-grade.
