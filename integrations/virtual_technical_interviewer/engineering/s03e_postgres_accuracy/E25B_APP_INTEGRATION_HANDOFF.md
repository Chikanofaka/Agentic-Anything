# S03-E2.5-B — Local PostgreSQL App Integration | Engineering Handoff

**Baseline:** E2.5-A feature commit `9aaaee49f7557b6f8b2582217df3dc4e848d5e68`.
**Expected Mac branch:** `feat/tia-s03e-e25b-app-grading-integration`.
**Scope:** Host-bound, native-confirmed, owner-reviewed fixture SQL accuracy within a single active three-question POSTGRESQL rehearsal. Neither an official LeetCode hidden-test checker nor competency/communication scoring.

## Product path

1. Prepare the 45-minute / POSTGRESQL / BYOQ configuration, explicitly confirm **three different questions**, start rehearsal, and Verify using your own API consent.
2. During a question, choose response type **SQL submission**, paste the query as raw PostgreSQL SQL, and send to the interviewer. The same text becomes a real candidate `implement` event.
3. In the local accuracy panel, copy the exact **current question SHA-256**. Prepare a `tia-postgres-fixture/v1` fixture with this digest, sample table definitions, rows and **human-reviewed expected output**. It is not enough to reuse the built-in demonstration JSON with placeholder question hash.
4. Paste JSON (<=12 KB), **Inspect**. Host compares the fixture question digest with the current question, and binds the resulting exact Fixture hash to the latest `implement` event and SQL hash.
5. Review every expected row; check the review box, click **Approve & run** and separately accept the macOS **native OS alert** showing three SHA digests.
6. Host executes the recorded SQL on an ephemeral PostgreSQL instance in a low-privilege, read-only role and journals a typed source-bound observation. It is never added to model dialogue or replayed as a live call.
7. Finish the question; verified local fixture results, candidate event, elapsed time and question SHA are frozen with the question's receipt. Next question starts clean.

## Hard gates / negative cases

- Wrong question SHA, stale candidate submission or fixture mismatch: **no PostgreSQL call**.
- Missing server or invalid candidate SQL: `NOT_VERIFIED` / typed execution error, not a guessed score.
- One successful or failed verified fixture grade **locks that question**; no gaming retries.
- No SQL `implement` event, unverified AI session, inactive question, or pending native request: **no grade**.
- Expired session / clock hold, including a DB response just after the 45-minute deadline: **no retroactive pass**.
- Journal replay/restore: **no PostgreSQL process may launch**; locally stored, SHA-bound observation reappears without mutating evidence.
- Candidate submission code, fixture answer and PostgreSQL result must not be included in model prompt beyond **candidate's own submitted message**; the Fixture and its expected output never reach the model.
- Native confirmation is required on real macOS. Test-only synthetic confirmation mode uses MOCK HTTP and a temporary isolated App save.

## Automated gates

From repository root:

```sh
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E25B --ui --regressions
```

The verification script should report the prior ten Mac groups and a new
`native-postgres-grading-webkit PASSED` group. In this last group, PostgreSQL
itself runs while OpenAI requests are **only MOCK_HTTP**. Native AppKit/WebKit
cannot be compiled by Linux checks; Python/unit tests and Swift syntax-only
validation are preliminary and **must not** be reported as Mac UAT success.

Only after Mac passes, review precise changed files, credentials and generated
logs. Stage approved **source and tests only**, not personal recordings, private
Fixture content or captured UI screenshots. Commit/push the feature branch only
with explicit review. Main merge and official scorecards remain gated.

## Known MVI limitations

- A single human-reviewed Fixture per question; no official hidden test corpus.
- Fixtures must be manually prepared by the user (the App does not parse a
  LeetCode webpage into executable Postgres seeds or infer trustworthy expected
  results). JSON paste bound is 12 KB to remain within existing IPC limits.
- The temporary-cluster runner is locally isolated with SQL restrictions and
  low privilege, but it is not a certified untrusted-code sandbox.
- A local PostgreSQL execution may take up to ~115 seconds. The Worker timeout
  is extended **only for `grade_execute`**; other actions remain at 15 seconds.
- The interactive evaluator is PostgreSQL-only. Pandas remains `NOT_RUN`.
- `Technical` and `Communication` official statuses remain `NOT_SCORED`; E3
  will build a separate evidence-based rubric and independent Trainer review.
- Local wall-clock integrity is not certified anti-cheat proctoring.
