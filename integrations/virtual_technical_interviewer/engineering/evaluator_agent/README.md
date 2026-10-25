# Independent Evaluator MVF — PRD v3

The completed three-question rehearsal now offers a separate, evidence-linked AI Evaluator for each question that has candidate evidence. The native API Portal owns credentials and paid consent; Python prepares and validates the frozen evidence; WebKit displays the result. Original SQL verdicts and interview receipts remain unchanged.

## Owner-confirmed policy

On 2026-10-25 the owner explicitly selected the PRD v3 **11-criterion** proposal for this operating agent and retained the **12-metric 70/20/10** code as an experiment. The latter is neither the current scoring baseline nor an automatic migration source. Historical labels in its compatibility schemas do not override this decision. Its imputed 50/100 and synthetic ratings never become canonical evaluator results.

Sources: `TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md` §14A, `RUBRIC_60_40_PROPOSAL.json`, and `DECISION_REGISTER.md` D02–D04/D10. The installed JSON is an exact copy of the canonical proposal. Hash-pinned identity, soul, AGENTS and skills compile into a distinct Evaluator prompt.

- Technical: T01–T05, proposed maxima 24/13/10/9/4.
- Communication: C01–C06, proposed maxima 6/7/7/9/7/4.
- Host arithmetic: `observed provisional points = criterion maximum × anchor / 4`.
- Missing evidence stays `NOT_OBSERVED`, never zero or renormalized. Technical and Communication totals/coverage are separate. No composite grade or mentality bonus.
- Models propose anchors, reasons and allowed candidate citations only. No model-supplied points, SQL verdicts, tools or host decisions are accepted. Source-bound citations establish provenance, not semantic truth.

## Working journey

Build from the repository root:

```sh
bash integrations/virtual_technical_interviewer/scripts/build_app.sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

Complete the three-question rehearsal, then select a question in **Independent AI Evaluator** on the completion report. Review the native disclosure and authorize one request. A fresh/reconnected credential is unverified until a successful response; each attempt consumes the native session cap, including cancelled/invalid replies. There is no automatic retry. The user may review source excerpts, proposed anchors, arithmetic, missing dimensions, model usage and prompt/rubric hashes, then export the session using the existing export control.

Native prepare → bounded HTTP → commit uses a request ID, generation token and frozen-question hash. The evaluator has no SQL runner, protected reference answer, credential or hint authority. Duplicate, stale, malformed and cross-question citations are rejected. A committed evaluator artifact is immutable and journalled separately. Crash recovery cancels pending evaluation. A broken evaluator source package leaves unrelated active/legacy interview records readable while blocking evaluation.

## Reproducible verification

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py \
  --increment S03-E3D --ui --regressions --voice --evaluator \
  --run-label YOUR_NEW_RUN_LABEL
```

Automation uses only synthetic credentials, mocked provider HTTP, synthetic voice and temporary local PostgreSQL fixtures. The evaluator App journey checks real PostgreSQL evidence, cancellation, malformed response rejection, reconnect/verification, cited assessment, arithmetic, duplicate/private-command rejection, compact layout and restart recovery. Other retained experimental transport tests use a loopback-only HTTP server. See `verification/` for measured results, not semantic-quality claims.

## Human UAT gate and limits

No paid evaluator call or human quality approval has been performed by this work. For paid UAT, obtain explicit owner authorization naming the model and request cap; use one already-closed question with consented non-sensitive content. A useful initial cap is one evaluator request. Check each proposed anchor against the displayed original citation, especially after assistance, and record disagreements without editing the frozen source.

This slice reviews completed three-question rehearsals only. Timed-out/integrity-held sessions remain readable but cannot request evaluation. Evidence is bounded (latest 16 candidate excerpts and up to 6 relevant interviewer excerpts); truncation is explicit. C06 has no explicit closing-speech event and abstains; anchor4 requires unfamiliar-task evidence absent here and is blocked. A single local SQL fixture is not proof of general correctness. Final grades stay `NOT_SCORED`; the 60/40 rubric and subweights are uncalibrated proposals. No approval/dispute workflow or automatic promotion into Trainer judgments is implemented. Trainer continues to use its separately authorized original evidence. Existing evaluator journals require their pinned source version for replay; source-version migration is a later slice.
