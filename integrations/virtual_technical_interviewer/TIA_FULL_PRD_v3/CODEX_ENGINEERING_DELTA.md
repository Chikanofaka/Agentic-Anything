# Codex handoff — apply full baseline to existing parallel discovery

**Do not restart from the rapid PRD and do not cancel verified compatible work.** Your job is a bounded delta reconciliation: identify existing work based on the rapid note, compare it to the full PRD/source hierarchy, and report incompatible assumptions before coding changes. This document is **not** permission to force push, purchase API tokens or publish sensitive transcripts.

1. Read `TIA_FULL_BASELINE_PRD_v3.md` in full, then `COMMUNICATION_EXAMINATION_MATRIX.csv`, `TRACEABILITY_SOURCE_TO_REQUIREMENT.csv`, `DECISION_REGISTER.md` and the repo's actual `AGENTS.md`/HAL domain package contracts. If a private original is available in your secure workspace, inspect it there—never commit it.
2. Produce `BASELINE_DELTA_RECEIPT.md`: existing branches/commits, tests run, reusable parts, conflicting former guidance (especially 40/20/25/15), new P0 needs, and unresolved owner decisions. Cite actual SHA and test run logs, not intention.
3. Implement the requested **one complete vertical slice**: interviewer admin + approved context → clarify/plan/execute/test/second-turn feedback and recovery → versioned 60/40 candidate evidence → explainable reviewer screen → separate trainer drill → held-out retry. Ensure Communication is present as behavior and technical action, not just a score label.
4. Use existing governed HAL `hal-domain/v1` package / host guards. Keep interviewer/trainer states and confidential answer vault separated, implement predeclared help permissions, host-owned time, events and scores.
5. Produce agent markdown (identity.md, soul.md, AGENTS.md, user.md, trainer.md) and a machine-checkable source-to-graph-to-agent-to-rubric trace. These prompt files never replace runtime authorization.
6. Run targeted scenario UAT in §28A plus domain and Witness regression tests; mark each `RUN/PASS/FAIL/SKIPPED/NOT_RUN` with artifacts.
7. Present changes at Human Gate. No unapproved external publication, paid model, video/voice capture or storage of private source.

**Response schema:** `Scope understood` → `Reused work` → `P0 gaps` → `Implementation plan & files` → `Commands executed` → `Tests and receipts` → `Open decisions` → `Human Gate request`.
