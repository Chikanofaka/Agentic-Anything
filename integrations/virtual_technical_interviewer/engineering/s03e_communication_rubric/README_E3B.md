# S03-E3B · Source-grounded communication rubric (provisional)

**Engineering parent:** `c158b04795af68af8bddb4c79631e3308ec962b1` on `feat/tia-s03e-e3-evidence-scorecard`.

**Target branch:** `feat/tia-s03e-e3b-communication-rubric`.

**Source alignment:** `TIA_FULL_BASELINE_PRD_v3.md` §§10A, 14A, 16A and `COMMUNICATION_EXAMINATION_MATRIX.csv` supplied for TIA. The PRD's 60/40 split is a **baseline hypothesis, not a calibrated score**. Its detailed C01–C06 weights and anchors remain engineering proposals; we have **not** approved or calculated a communication mark.

## Done in this increment

- `communication_rubric.py`: six explicit proposed C01–C06 dimensions (6/7/7/9/7/4). Reproducible local snapshot and export from the saved three-question journal; each potential observation cites an actual candidate Event ID, text hash, bounded source excerpt, and separate question index.
- Clear `NOT_OBSERVED` vs `POTENTIAL_EVIDENCE_NEEDS_SEMANTIC_REVIEW`; all numeric competency fields stay `NOT_SCORED`/`NOT_EVALUATED`. The `0–4` rubric anchors appear **as a proposal only**. There is no aggregate score, personality inference or mental impression bonus.
- C05 shows a **sequence only** when a genuine committed interviewer reply is followed by a candidate `plan`/`implement`/`test` action; it never infers that feedback was understood, incorporated, or tested successfully. “I understand” alone is insufficient.
- C06 remains `NOT_OBSERVED`: Finish is a Host action, not a spoken closing synthesis. This is a documented schema gap for later instrumentation, not an automatic zero.
- The live rehearsal UI shows a compact communication *strategy* checklist; after completion the six dimensions appear per question with event references and evidence excerpts.
- `validate_review_proposal` is a strictly bounded, source-cited interface for **future** model/human reviewer proposals. It rejects missing, mismatched and cross-question Event IDs, evidence checksum drift, unobserved dimensions, invalid anchors, fabricated rater authority and inadequate reasoning. Even syntactically valid proposals always remain `PENDING_HUMAN_REVIEW` and cannot score the candidate.
- No SQL engine, paid OpenAI call, network request, trainer, approval workflow or saved-state schema migration is introduced. Legacy E1/E2/E25/E3A records continue to reopen via deterministic journal replay without regeneration or reassessment.

## Not done (E3-C / dedicated subsequent gates)

Actual rubric **quality grading** (0–4) is not enabled; event kinds alone cannot establish helpful clarification, truthful diagnostics, adaptation to feedback or a competent closing statement. A new explicit closing speech event (or equivalent source-backed artifact) is necessary to evaluate C06 rather than guessing. Assessor-model transport, meaningful contextual ratings, conflict adjudication and human review UI are future work. The 60/40 weights and any 10–15 point impression bonus remain uncalibrated and unapplied. Nothing here is a hiring decision.

## Verification

1. Python unit + Host/recovery tests: `python3 -B integrations/virtual_technical_interviewer/run_tests.py` (expected **229 tests**, including 22 new E3B tests).
2. On macOS with PostgreSQL 17 server binaries already available:

   ```bash
   python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3B --ui --regressions
   ```

   The `native-communication-rubric-webkit` gate uses Mock OpenAI transport and a real **local ephemeral PostgreSQL** fixture. It checks a native consented Q1 SQL PASS, skipped Q2/Q3 not inheriting grades, existing E3-A technical report and E3-B six-dimension communication evidence UI, with no numeric communication mark. Do **not** enter real API credentials in automated windows.

3. Check export and app-recovery: the `communication_evidence.sha256` is stable, without replay of SQL or provider calls. This is a **local checksum**, not a cryptographic attestation.
4. Only after Mac PASS, stage the exact E3B engineering changes, review for secrets/local personal content, Commit and Push to the E3B feature branch; **do not** automatically merge to `main` or upload generated verification screenshots/logs.

## Interpretation guardrails

- This is an evidence map, not a competency score. We deliberately do not treat the number of help requests, words, turns, planning statements, or politeness as positive communication.
- A real interviewer reply followed by an SQL attempt is chronological, not proof that the attempt implemented the advice.
- All cited snippets derive from candidate-entered text already held privately in the App; local export contains personal text and should be handled privately.
- No protected characteristics, inferred personal qualities, accent or emotion are evaluated.
