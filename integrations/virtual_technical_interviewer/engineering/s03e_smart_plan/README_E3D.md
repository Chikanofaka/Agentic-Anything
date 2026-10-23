# S03-E3D — Evidence-Linked Seven-Day SMART Improvement Plan

**Stage:** increment proposed for native macOS acceptance; NOT a scored competency or verified learning gain.
**Base:** `fead45ff800b54f2dee0603a1e757998817e5e8c` (E3-C-B, pushed to GitHub).
**Branch:** `feat/tia-s03e-e3d-smart-improvement-plan`.

## In scope

- A deterministic, bounded `tia-smart-improvement-plan/v1` projection from the completed rehearsal and the E3-C-A grounded drills. It is anchored to **both** the original trainer SHA and the frozen rehearsal SHA. The first three priority drills generate at most three SMART goals (specific action, measurable acceptance, bounded achievable task, relevant source evidence, 1/3/7-day time bound).
- The **user explicitly starts** a 7-day plan. Host supplies `started_wall_seconds` and stable deadlines from a journalled wall timestamp, never a WebKit clock; no deadlines exist before that action.
- User records `PRACTICED`, `BLOCKED`, or `RETEST_RECORDED`. Journal entries include task ID, limited note, optional *self-reported* artifact SHA, Host timestamp and an explicit `SELF_REPORTED_UNVERIFIED` disclaimer. Up to 8 entries per goal and 24 total; no arbitrary paths or URLs.
- Host validates exact command fields; Native Bridge mirrors the narrow renderer permission. No native-only, SQL, model, grader, file-picker or credential authority is granted by SMART commands.
- Save/journal replay restores progress and preserves prior interview evidence. Prior-save state digests are unchanged until the first user-start action. New journal events participate in the Host state checksum.
- App completion page displays task, due time, source event IDs, attempts and provenance. Export contains the same state. There is no automatic provider call, billable prompt, scored ability, SQL execution or employment decision.
- Native test `--ui-smart-test` reuses the existing synthetic 3-question BYOQ SQL fixture path and Mock HTTP. It verifies source binding, initial unstarted state, explicit start, one practice log, a hash-required external retest log, and no mutation of the technical scorecard.

## Truthfulness rules

1. **Practice attempted** is not **task completed**, and neither is **ability improved**.
2. An artifact digest pasted by the candidate is **not independently verified** merely because it is a valid SHA-256 string.
3. An earlier approved local fixture PASS is not an official hidden-test result, and is not a new training result.
4. The candidate's training notes are untrusted. They cannot create events for a non-existent goal, change the frozen interview, assign a competence grade, or fabricate a source receipt.
5. AI Trainer proposals remain `PENDING_HUMAN_REVIEW` and are *not* automatically adopted as SMART goals.
6. A real new, independently authorized retest, comparison to a held-out baseline, and review must be built and accepted in a later stage before using language like “verified improvement.”

## Tests and Human Gate

Run on macOS after applying E3-D incremental patch:

```bash
cd ~/Developer/Agentic-Anything
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3D --ui --regressions
echo "E3D_MAC_GATE_EXIT_CODE=$?"
```

Expected dedicated check: `native-smart-plan-webkit PASSED`. The full test script will also run native build, prior WebKit, mock live, recovery, Provider failures, rehearsal, and Witness/HAL. The automated test must have **zero real OpenAI requests**. Generated `verification_E3D/` is excluded from the source-stage git commit until an explicit privacy decision.

**Outstanding:** Real OpenAI paid Trainer UAT still not run; human end-to-end 45-minute interview UAT still not run; fresh held-out SMART retest and verified causal learning measurement **not implemented**. No merge to `main` is authorized by installing this patch.
