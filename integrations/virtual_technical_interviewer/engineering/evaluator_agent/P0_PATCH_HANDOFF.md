# Final P0 product patch — engineering handoff

Date: 2026-10-27 (Asia/Shanghai). Branch: `feat/tia-evaluator-agent`.
Parent commit: `d3b7f8c136eadc7b7328b83f8a73c29124f5661b`.

**Local implementation and automated integrated verification are complete. Human end-to-end UAT remains NOT_RUN.** This patch is deliberately uncommitted. No push, release, formal-grade approval or paid provider call was made. Existing historical receipts, user sessions and role/rubric sources were preserved.

## Resulting behavior

| Requirement | Implemented behavior and main sources |
|---|---|
| P0-01 continuity | New sessions use `tia-continuity/v3`, with continuous conversation throughout each independent 900-second question window. No numerical replacement turn/event/journal cap. Only explicit Final Submit, manual Skip or Host timeout advances. Model/capacity errors remain explicit without closing the question. Submitted code remains finalizable after later discussion. `app_host.py`, `controller.py`, `time_intelligence.py`, `host_adaptive_bridge.py`, `rehearsal.py`, Native bridge and UI. |
| P0-02 silence seal | Native monotonic acoustic-activity clock requires at least five uninterrupted seconds of silence and nonempty text. Resumed candidate speech resets it. Recognizer finalization alone cannot send; stale timers/final callbacks cannot duplicate delivery. `native/Voice.swift` and voice tests. |
| P0-03 barge-in | With granted permissions, the native echo-cancelled input detector stays active during playback. Sustained candidate onset interrupts local speech; the same silence gate then seals candidate text. Asking to skip an introduction stays ordinary dialogue and cannot invoke Skip Question. Defaults remain automatic sending, minimized companion and Faster. Real acoustic performance still needs device UAT. |
| P0-04 private oracle | Native sealed source-bound proposals can be checked for each of all three questions against separately approved independent local PostgreSQL fixtures. A dedicated one-shot verifier receives code only through stdin and returns bounded hash/status facts. All approaches must pass before a question becomes verified. Missing/failed execution remains unverified. No reference text reaches regular Host/WebKit/export/argv. `NativePreparer.swift`, `main.swift`, `private_oracle_worker.py`, `sql_accuracy.py`. |
| P0-05 evaluator | New v3 evaluation sends complete ordered candidate/interviewer dialogue, preserving full text and citations. Capacity failure is explicit before any request, never silent truncation. All 11 PRD v3 criteria remain; verified candidate execution is authoritative. Bilingual evidence gates reject known unsupported claims without certifying model judgment. `native_evaluator.py`, `evaluator_p0_guards_v2.py`, evaluator-only Native request envelope. |

## Verification

The final [integrated receipt](verification/p0-integrated-20261027-02/receipt.json) records **18/18 passing groups**, including App build, actual WebKit windows, setup, mock provider failures, three-question continuity, local PostgreSQL grading, voice, adaptive interruption/recovery, private preparer, evaluator/recovery, Witness and shared HAL.

- Python: 848 tests run, 0 failures, 1 skipped. The skipped experimental browser-DOM test requires Node.js, unavailable here; the actual native WebKit suites passed separately.
- Build self-tests: 151 Native, 76 mocked Provider and 133 synthetic Voice checks passed.
- Additional [native oracle run](verification/p0-integrated-20261027-02/native-oracle.txt): 159 Native checks passed, including real local verification for Q1/Q2/Q3, private-output isolation and cancellation rejecting a late commitment. Same final App build; zero real provider requests.
- Witness/shared HAL: 287 Python tests and 52 native checks passed.
- Legacy replay: a captured pre-P0 synthetic v2 journal restores its original state digest exactly. v2 evaluator inputs and artifacts match the d3b7f8c implementation; old rules are not reinterpreted as v3. Legacy no-policy tests remain passing.
- Full-context regression retains 140 chronological conversation events; exceeding the explicit byte capacity rejects the request without mutating the frozen interview.
- All recorded source hashes and packaged resource hashes matched at handoff. `git diff --check` passed.

The first integrated run is retained as evidence: its voice test incorrectly clicked Final Submit without code. The corrected test verifies Final Submit is disabled, explicitly skips, and still proves frozen transcript / rejected stale speech. No production authority check was weakened.

## Reproduce and open

From this worktree:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3D --ui --regressions --voice --evaluator --run-label p0-repeat-unique-label
```

The label must be new to preserve earlier evidence. This command uses isolated synthetic sessions, mocked HTTP and local PostgreSQL, and drives its own windows. Do not click those automated windows.

Development App: `integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app`.
Exact changed paths, source hashes and final binary identity: [P0_PATCH_FILES.json](P0_PATCH_FILES.json). This manifest describes the entire working patch, including pre-existing continuity edits preserved at task entry; it is not a new commit SHA.

## Remaining acceptance and practical limits

Use [P0_HUMAN_UAT.md](P0_HUMAN_UAT.md) for one complete human interview-to-evaluation run. Test built-in speakers and headphones, first-use permissions, real five-second timing, interruption and first-syllable retention, six-plus exchanges, all three closure paths, independent fixtures and evaluation citations. No agent paid-call authorization is granted by this handoff; any agent-driven real test needs separate explicit model and request-limit approval.

- Unlimited conversation does not remove native paid-request consent caps or per-request/storage byte limits. Failures must be visible and must not advance a question.
- Apple on-device recognition and Voice Processing I/O must be available. Synthetic tests cannot establish echo rejection or speech detection quality on the user's hardware.
- PostgreSQL verification needs independently reviewed, exact-source-bound fixtures and approved local binaries. Pandas execution remains unavailable; proposals without execution stay unverified. Passing reference tests does not grade candidate SQL or establish official hidden-test correctness.
- Private reference material remains native memory only and is cleared on disconnect/quit. It is not restored with historical transcripts.
- Complete evaluator input is bounded at 256 KiB; over-capacity evaluation fails explicitly. Model semantic quality and evidence applicability still need human review. Proposed arithmetic is separate from formal Technical/Communication/Overall grades, which remain `NOT_SCORED`.
- Request counts exported from Native are labeled as an App-process snapshot, not a reconstructed lifetime interview total. Unknown persisted totals remain null rather than a false zero.
