# TIA S03-E3A — evidence-only scorecard (feature branch candidate)

## Purpose and boundaries

E3-A is **not** a numerical ability score, LeetCode official correctness grade, communication judgment, or live Trainer. It is a reproducible **read-only projection** from the journalled three-question rehearsal: frozen submitted SQL, a human-approved local Fixture, an ephemeral PostgreSQL result, raw candidate-event IDs, and the host-owned local time ledger.

`evidence_scorecard` is returned in the Host `snapshot` and explicit `export` of a three-question rehearsal. It is not a new authority or a second persistence channel. `_state_digest` intentionally excludes this additive projection so E1/E2/E25B saves remain readable and retain their original exact digests. Reload never executes SQL, sends an OpenAI request, or modifies old receipts just to display the scorecard.

## Evidence policy

- All three questions appear with a closed/active/not-reached distinction. No score is assigned to an unanswered question.
- Each completed question reports actual `clarify`, `help`, `implement` and candidate-turn counts from **candidate event IDs**. Counts are descriptive; they cannot measure communication quality.
- A PostgreSQL `PASSED`, `FAILED` or `EXECUTION_ERROR` verdict is counted only when the receipt contains an exact **question hash, candidate implementation event ID, SQL hash, Fixture hash, native human approval, real isolated Postgres provenance** and a single approved local Fixture result.
- If the candidate submits a newer SQL implementation after a verified result, the *latest SQL* is `NOT_VERIFIED`. The prior fixture observation remains traceable but is not counted as proof for the final SQL. Skipping the question also prevents final-submission credit.
- Unavailable backend, missing Fixture, mismatched evidence, legacy ungraded rehearsal and never-reached questions remain `NOT_VERIFIED`, not `FAILED` and not `0%`.
- The scorecard deliberately has **no percentages, 60/40 weighting, numerical capability score, interview hire/no-hire recommendation, or fake hidden-test pass rate**. `technical_capability`, `communication_competency`, `overall_grade` remain `NOT_SCORED`.
- Time is local host-owned, includes model wait, and remains `LOCAL_UNATTESTED`. No proctoring certificate is claimed.
- The scorecard has a deterministic local SHA-256 **checksum**, not an independently signed attestation against a malicious local file owner.

## Files / entry points

- `tia_runtime/evidence_scorecard.py`: deterministic projection, latest-submission truth guard and source event identifiers.
- `tia_runtime/app_host.py`: state/export read-only scorecard; compatibility exclusion from saved state digest.
- `ui/app.js`: accessible collapsible per-question evidence and summary on the completed-rehearsal screen; English and Chinese labels.
- `tests/test_s03e_evidence_scorecard.py`: 17 new Python tests, including live Host journal recovery without a PostgreSQL rerun and stale code downgrade.
- `native/UISmoke.swift`: an additional evidence panel assertion after the real native PostgreSQL grading demonstration.
- `scripts/verify_app.py`: dedicated `S03-E3A` increment, with evidence in `engineering/s03e_evidence_scorecard/verification_E3A/` (generated files are not for unreviewed publication).

## Human Mac gates (no real paid API)

Run from the repository root:

```sh
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3A --ui --regressions
```

The second command **must be verified on macOS**, as it runs actual AppKit/WebKit and a private ephemeral PostgreSQL server with Mock OpenAI. It must demonstrate `native-evidence-scorecard-webkit PASSED`, including that Q1's verified Fixture does not produce grades for Q2 and Q3. Do not enter a real API key in these automated test windows.

**Release gate:** `190+17=207` Python expected (from E25B baseline), Native/WebKit required. Review generated evidence and exact staged file list, perform secret/privacy scan, commit only approved source/docs/tests, push the `feat/tia-s03e-e3-evidence-scorecard` branch. Do not merge to `main` or publish a signed app without a separate user approval.

## Later increments

E3-B: communication **evidence and structured rubric** with traceable evaluator provenance and explicit uncertainty. E3-C: separately authorized Trainer and SMART plan, grounded in both real test results and labeled qualitative interview observations. No numerical weighting until justified and accepted.
