# S03-E3C-A — Grounded Trainer, offline training draft

**Parent branch SHA:** `612b45f2f36472da2c873b355d8c55726bdedde9`, `feat/tia-s03e-e3b-communication-rubric`.
**Target branch:** `feat/tia-s03e-e3c-evidence-grounded-trainer`.

## What is delivered

The Training Lab on the completed three-question rehearsal now produces a deterministic,
**read-only** training assignment from authentic E3-A technical evidence and E3-B
C01–C06 communication evidence. The Host returns it in `grounded_trainer` in both
snapshot and explicit local export. The packet cites the SHA-256 digests of both
source views. Its question drills cite only actual candidate Event IDs and approved
local fixture IDs (when available), carry measurable independent retest tasks,
keep `NOT_SCORED`, and **never** claim that a single local fixture represents
formal or hidden-test competence.

Priority observations: tested SQL is now stale → recheck newest code; real local
fixture mismatch → isolate and reproduce; execution error → debug the actual
error; untested final SQL → create an approved fixture; single passed fixture →
expand coverage; insufficient data → fresh first attempt. C06 is an optional
closing-speech *instrumentation gap*: the current app cannot determine closing
competence from a Finish-button click. These are training **opportunities**,
not verified causal diagnoses. Each task is unattempted until a distinct future
training/assessment workflow captures new evidence. `next_question_policy`
asks for a **fresh, held-out** skill-aligned question rather than reusing the
same question as proof of improvement.

`validate_trainer_model_proposal` is a bounded, provenance-checked interface
for a **future** AI trainer draft. It rejects fabricated/cross-question events,
wrong trainer/evidence digests, bad fixture IDs, unauthorized drill tags and
oversized claims. Format/citation validation **cannot** prove semantic quality.
Even a syntactically valid AI proposal is `PENDING_HUMAN_REVIEW`, never a
performance score or binding diagnosis. There is **no actual model request**,
no provider credential read, no completed SMART schedule and no verified
post-training learning gain in E3C-A.

## Next controlled E3C-B gate: real paid AI Trainer

An actual OpenAI Trainer requires a distinct native Host prepare/commit protocol,
explicit paid-request consent, minimum transcript disclosure with a privacy
preview, strict native output schema and source-bound proposal validation,
restoration-safe idempotent response receipt, budget/cancellation handling,
mock-HTTP negative testing, and independent Mac UAT. No renderer-only network
call or fake "AI generated" claim is permitted. This is **not** authorized or
implemented merely by E3C-A's training view.

## Tests and Human Gate

From the root of the user repository, after installing the incremental patch:

```sh
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3C --ui --regressions
echo "E3C_A_MAC_EXIT_CODE=$?"
```

Expected locally: 257 Python tests, Native build, existing WebKit/PG/Mock HTTP
regressions and `native-grounded-trainer-webkit`. The Mac UAT uses *zero real*
OpenAI API calls. No Mac AppKit test has yet been performed in the patch-build
environment; the user must run it before any GitHub Commit/Push.

Generated `verification_E3C` screenshots and logs are local and may contain
private machine details; do not include them in public commits by default.
The E3B verified private save/checksum is unchanged by the trainer projection.
