# Evaluator MVF handoff — 2026-10-25

Branch: `feat/tia-evaluator-agent`, based on voice commit `44ad23d`. This local commit contains the implementation, preserved offline experiments and sanitized executable evidence. No push, release or real paid API call was made. Original checkout and voice branch were not modified.

The owner confirmed **PRD v3: 11 criteria, proposed Technical60 / Communication40**. The operating agent accepts immutable question evidence, returns cited proposed anchors, and lets the host compute separate provisional points and missing-evidence coverage. The12-metric70/20/10 implementation remains an explicitly separate experiment; its imputed/synthetic totals do not enter the canonical evaluator.

Implemented: pinned independent role instructions; private native prepare/call/commit; per-question native consent; fixed bounded provider transport; cancellation/late/duplicate/malformed rejection; readable original records on optional-source failure; completion UI, citations, export and restart recovery. Model responses remain proposals requiring human review. Original SQL verdicts/receipts are preserved, final scores remain NOT_SCORED. No calibration or human semantic approval is claimed.

## Actual verification

[Full receipts and exact commands](verification/evaluator-mvf-20261025-01/receipt.json): **18/18 groups passed**.

| Suite | Result |
|---|---|
| TIA Python, including preserved experiments | 765 run:764passed,1skipped;0failures |
| Native contracts | 143passed,0failed |
| Provider mock transport | 72passed,0failed |
| Local voice unit checks | 108passed,0failed; no real microphone/audio |
| Actual WebKit/native/controller journeys | 140passed,0failed, including18evaluator/recovery checks |
| Witness native | 52passed,0failed |
| Shared HAL/Witness Python | 287passed,0failed |

The single skip is an experimental Node.js browser-DOM simulation because Node.js is absent. Actual native WebKit journeys passed. Evaluator UAT uses real temporary PostgreSQL execution plus mocked model responses: cancel, malformed reply, reconnect from unverified to verified, immutable citation/point commit, skipped-question refusal, duplicate rejection, compact layout and recovery without another request. These checks validate execution and boundaries, not AI assessment accuracy.

## Open and use

From this worktree root:

```sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

Complete the three-question rehearsal and select **Independent AI Evaluator** in the completion report. Follow [the operating guide](README.md) for consent, privacy and limits. The next smallest step is owner-authorized real-model UAT on one closed question, with an explicitly selected model/request cap and human comparison of each cited judgment. No paid UAT is authorized by this receipt.

[Exact changed-file inventory](CHANGED_FILES.json). Earlier unlabelled verification receipts and native `.bak` files remain outside this commit; they were preserved in place. Source hashes in the labelled verification receipt match the tested source at handoff; `.bak` hashes are inventory-only, not build inputs. Persisted evaluator journals currently need their pinned source version; schema/policy migration is future work.
