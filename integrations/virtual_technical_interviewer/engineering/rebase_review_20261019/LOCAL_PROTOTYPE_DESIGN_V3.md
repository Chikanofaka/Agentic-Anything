# Technical Interviewer Agent — local design rebased to v3

**Date:** 2026-10-19. **Status:** design and acceptance planning only. No application, prompt package, SQL evaluator, or live agent is implemented by these deliverables. All application/UAT statuses remain `NOT_RUN`.

## 1. Baseline, changes and scope

**[SOURCE / current user instruction]** This design reads the entire `sources/TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md` and its Communication Examination Matrix, rubric JSON, UAT matrix, traceability CSV, Decision Register and Codex Engineering Delta. The source package is associated with parent-verified remote revision `53188034400be6c534d2ded56a9386ea55d6ad0e`. Original intent and explicitly accepted later instructions remain highest authority, followed by accepted reviews and the draft Atlas. v3 supersedes the Rapid PRD's conflicting requirements; the earlier discovery files remain preserved as history.

**[PROPOSAL]** Retain compatible prior work: offline adapters, independent technical/communication evidence, B05 correction, repeated interaction loops, missingness, disclosure controls, immutable receipts, and a two-session training loop. Rebase old test IDs rather than interpreting the earlier `FR01–FR10` as the differently numbered v3 `FR-01–FR-28`.

| Earlier design | v3 design treatment |
|---|---|
| Configurable 60/40 | Retain confirmed top-level training hypothesis; add explicit v3 subweights/anchors as **unapproved fixtures** |
| Optional 0–10 bonus | Superseded. **10–15 hypothesis, disabled; no deployed formula or automatic award** |
| Scripted outcome demonstrator | Retain as policy rehearsal, clearly `SIMULATED`; it cannot meet real SQL M0 acceptance |
| Per-phase communication slots | Expand to 12 COM-FR requirements, 16 exam checkpoints, technical-action links and reviewed training memory |
| Broad prompt/governance proposal | Add versioned source→graph→agent→host→rubric→trainer trace and profile-approved context |
| Variant second question | Require held-out item/attempt tracking, difficulty and assistance comparability; no transfer claim from repetition |
| Local history | Add consent snapshots, opt-out/minimization, deletion, appeals, interruption/idempotency and explicit failure states |

**[SOURCE]** v3 §§16,19,26 and the Delta call for a later real, governed HAL Type B vertical slice. **This turn's scope is rebase/planning documents only**; those instructions do not turn these plans into implementation receipts. No API, external publication, deployment, paid provider, raw-source export, arbitrary Python, new domain registration, or prompt-file creation occurs here.

**[SOURCE + OPEN]** v3 has internal historical remnants: a v2 footer; §31 Q07 mentions preserving an old four-factor alternative despite §14/Decision D-10 rejecting it as current baseline; §26 and §26A reuse G-numbers for different stage descriptions. Follow the explicit reconciliation notice, §14A and Decision Register; namespace future gates as `PRD26:Gx` / `PRD26A:Gx` until consolidated. Do not activate 40/20/25/15. Review identifiers cited in v3 establish its current communication requirement but do not recreate missing original dialogue or prove every historical review was recovered. The previously supplied review-named PDF was an Atlas draft export, not a review transcript. These source gaps do not block explicit v3 planning.

## 2. What the future local slice must demonstrate

**[SOURCE: FR-01–FR-14, FR-25, FR-27–FR-28; COM-FR-001–012]** One user can configure an interview, approve the relevant profile context, clarify/plan/code/test, encounter policy-governed feedback and a second/third decision round, close, inspect separate technical and communication evidence, challenge a judgment, accept one targeted drill, and attempt a fresh held-out question. No-key use must be meaningful. SQL correctness must come from an actual reviewed local evaluator for `M0_ENG_DONE`; dialogue can remain scripted and labelled.

**[PROPOSAL]** Use terminal or existing reviewed HAL local UI/IPC initially. Do not assume a new package directory is executable or expose an unauthenticated localhost service. Keep three layers: versioned data/assets; trusted decision/evaluation/receipt host; filtered candidate/review/trainer views. The selected transport is an implementation decision after repository audit.

| Mode/component | Actual capability | Required provenance |
|---|---|---|
| Scenario adapter | Replays pre-authored turns and supplied outcomes | `SIMULATED`; supplied outcomes are not executed test evidence |
| Manual adapter | Human supplies text and an operator selects permitted reactions/labels | `MANUAL`; rater identity, method, confidence and cited spans |
| Real offline SQL evaluator, later | Executes restricted query against versioned fixtures | `TEST_VERIFIED` only with actual execution receipt; surrounding dialogue may still be simulated |
| Provider adapter, later separate gate | Authorized bounded generation | Actual provider receipt; `MODEL_PROPOSED` observations are not host verdicts |

Component-level labels must survive UI, exports and replay. A failed live request cannot silently become simulated. A nonfunctional key field does not establish provider access. Fixture contract tests only establish their stated layer.

## 3. Two-session user flow

**[PROPOSAL implementing §§08–15,17]**

1. **Onboard and select context.** Explain practice versus hiring scores, mode, privacy and storage. User approves a minimal profile snapshot: target role/topic/level, language, style, aids, timebox and accommodations. Personal source text, visa details and previous interview anecdotes are not required; sponsorship context never contributes to competency scoring. Start only supported configurations. Empty licensed item pool is a visible inability to start, not an invented question.
2. **Brief and clarify.** Disclose format/time/tools/submission policy. Use corrected Atlas B05: unclear YES→clarify→recheck; clear NO→ability assessment. Clarification facts are separated from solution hints. Unclear or unobserved branch conditions are `UNKNOWN`, not false.
3. **Plan and implement.** Simple case permits a concise plan; hard case permits decomposition, invariant, first test and staged code. Record text/notes as communication and link them to actual work. Written notes and accessibility choices can substitute for constant speech.
4. **Observe a full reaction loop.** The interviewer can wait, clarify, challenge, ask a diagnostic question, request a test, give permitted help, decline, move on or close. Candidate response then produces a plan/edit/test or a precise unresolved gap. Observe the next action before claiming progress. Repeat blockage requires a new time/policy/diagnosis decision, not automatic escalation.
5. **Test and recover.** Execute safe SQL only through the reviewed evaluator. Keep public/hidden disclosure policy explicit. Contrast two 4/20 fixtures: one sorting defect versus a genuine structural deficit. Neither fraction establishes how much of the problem is solved. Preserve useful earlier artifacts; test the smallest proposed change. Actual SQL success does not establish communication quality.
6. **Close and review.** On submit/timeout/cancel, freeze the authoritative record. Late submissions do not edit it. Reveal versioned score evidence, assistance history, unknowns and a dispute action. A dispute adds a review record and possible new score version; it cannot rewrite the original execution facts.
7. **Trainer drill.** Only a committed, reviewed and consent-permitted packet reaches Trainer/memory. Trainer targets the smallest evidenced high-impact weakness, explaining both technical and communication causes. One example drill is to state verified progress, identify row-grain loss, propose a diagnostic test, implement a fix and explain the result. Coaching is not retrospectively scored as interview performance.
8. **Held-out retry.** Host selects a different licensed item not previously attempted or disclosed, using target skill tags rather than hidden answers. Store novelty, attempt count, difficulty, aids, rubric/weight versions, accommodations and rater confidence. Compare matched conditions; otherwise label limited/incomparable. An easier second item or memorized answer cannot prove unassisted improvement or transfer.

## 4. Declarative policy and role boundaries

**[SOURCE: §§08A,11–12,17–20; D-08/D-09]** B05 is corrected behavior, not a claim the Atlas image was modified. F01-002/F02-001 require complete walkthrough coverage. Failure to understand does not impose a duty to keep hinting. No 0.8/0.2 threshold controls passing, assistance or severity. Candidate persuasion cannot alter authorization. Unusual valid solutions are evaluated semantically, not by canonical string matching.

**[PROPOSAL]** A rule record contains `rule_id/version`, source anchors and status, graph/node IDs, named edge or explicitly proposed edge ID, actor/state, observable trigger, preconditions, confidence, branch condition including `UNKNOWN`, permitted/prohibited actions, context policy, disclosure scope, candidate next step, host effect, measured signal, rubric IDs, trainer tags, re-entry and time/consent termination. Zero matches return an unsupported-state result; multiple matches require a logged allowed operator/scenario choice or reviewed selection policy. Unverified policy thresholds are editable configuration with provenance, not hidden constants.

**[SOURCE / PROPOSAL details]** Hint ladder is versioned H0–H5: none, clarification, diagnostic question, conceptual contrast, method-family, explicit technique. Modes include UNAIDED, INTERVIEWER_HINTS, DOCUMENTATION_ALLOWED, AI_ASSISTED_PRACTICE and TRAINER_DRILL. H1 classification and H1–H3 defaults remain policy hypotheses. Request quality and allowed level are separate. The host atomically logs request→grant/deny→authorized disclosure→later assisted work. It owns the clock, revisions, permissions, test facts, score commits and final receipts. No model or prompt can grant itself authority.

**[PROPOSAL]** Prefer allowlisted clarification/hint blocks in the offline slice. Protect reference solutions and hidden tests in evaluator-only storage. Future model context excludes sealed answers; output filtering supplements context minimization and policy checks, never replaces them. Trainer obtains authorized teaching content for the completed item only; switching role does not open future answers. Prompt injection in candidate text, external documentation, model output or imported content remains untrusted data.

## 5. Communication and agent trace

**[SOURCE: §16A]** Every material turn needs actor, stage, state, time, evidence ID and technical-artifact linkage or an explicit reason no artifact yet exists. Preserve wording within consent. Distinguish plan from artifact, claim from proof, conceptual understanding from recall, recognition from action, and action from verified result. `AH_AHA_AND_CAN_EXECUTE`, `BH_UNDERSTANDS_GAP_BUT_NO_METHOD`, `CH_NOT_UNDERSTANDING`, `DH_NO_PROGRESS_AFTER_HELP`, and `EH_VALID_NOVEL_PATH` are distinct scenario states, not diagnoses of private thought.

**[PROPOSAL]** Use explicit namespaces: `exam:C01–C16` from the examination CSV, `rubric:C01–C06` from the scoring proposal, and `atlas:C01` etc. They are different IDs. Examination rows do not each earn their listed context maximum; several rows inform a single rubric dimension. This prevents accidental multiple counting of 6/7/9-point contexts.

| Exam checkpoints | Phase | Proposed rubric link | Required observation |
|---|---|---|---|
| C01–C02 | OPEN/CLARIFY | rubric:C01 | Terms, restatement, precise clarification, acknowledgment/action |
| C03–C04 | PLAN | rubric:C02; technical T02/T03 separately | Method, why operator fits, contingency and later code/test link |
| C05 | REACT | rubric:C02/C05 | Silence/challenge interpretation followed by a self-directed action |
| C06/C08/C09 | RECOVER | rubric:C04 | Gap type, independent diagnosis, bounded request and grant/denial |
| C07 | RECOVER | rubric:C03 | Done, tested, unverified, remaining; claims cite test/artifact |
| C10–C11 | REACT | rubric:C05/C04 | Recognition versus executable knowledge; action chronology |
| C12–C13 | TEST/RECOVER | rubric:C03/C05; T04 separately | Failure pattern, limits, hypothesis and actual recovery behavior |
| C14 | CONCLUDE | rubric:C06 | Honest synthesis, limitations and appropriate acknowledgment |
| C15–C16 | TRAIN | training tags, no new interview points | Explain evidence, choose drill, retest unfamiliar comparable item |

**[PROPOSAL implementing COM-FR-011/§18A]** Future prompt artifacts are versioned interfaces, not files created in this turn:

| Proposed artifact | Responsibility / permitted context |
|---|---|
| interviewer/identity.md | Professional role/style, current approved scope; no fabricated real-employer identity |
| interviewer/soul.md | Restraint, novelty fairness, honest uncertainty, communication conduct; no authority bypass |
| interviewer/AGENTS.md | Typed tool/input/output/routing contract under installed host capabilities |
| candidate/user.md | Explicitly approved preferences and scope with consent/version; no source transcript dump or HR scoring |
| trainer/identity.md + TRAINING_CONTRACT.md | Read-only reviewed receipt, allowed teaching pointers, drill/retest contract |
| policies/INTERACTION_RULES.yaml | Declarative rules consumed and enforced by trusted host |
| rubrics/COMMUNICATION_60_40_PROPOSAL.yaml | Versioned proposal subweights/anchors, applicability and confidence rules |

For every P0 communication requirement, the trace row must connect `source line/review → graph node/edge → COM-FR → prompt clause/version → input context → host check → event schema → rubric feature → trainer tag → positive/negative test`. Missing mappings are explicit uncovered items. Store prompt/rule/context hashes in each session snapshot. Editing a prompt does not change a frozen session or bypass a host check. Only a reviewed policy version becomes active; pending adversarial changes remain separate Plan 2 proposals with falsifiable tests and recorded owner decision.

## 6. Data, consent and immutable evidence

**[PROPOSAL implementing §§17–18A]** Core records are `CandidateProfile`, `ConsentSnapshot`, `ConfigSnapshot`, `VersionedQuestion`, `InterviewSession`, `ActionEvent`, `HintDecision`, `TestExecution`, `AssessmentEvidence`, `SessionReceipt`, `ReviewerAppeal`, `TrainerAssessment`, `TrainingAssignment`, and `DrillAttempt`. Separate public question, sealed key, candidate-private, reviewed evidence, trainer summary, credential and opt-in metric classes.

Session stores question/fixture/policy/rubric/weight/prompt/context versions, dialect, time markers, privacy/retention settings, mode and provenance. Commands carry expected revision and idempotency key. Event stores actor, phase, intent, node/rule, monotonic time, artifact references, completed claims and proof, unresolved gap, independent attempts, request scope, response, next action, assistance before/after and confidence. `USER_SAID`, `USER_DEMONSTRATED`, `MODEL_PROPOSED`, `TEST_VERIFIED`, `QUESTION_CANON` and `REVIEWER_OVERRIDE` remain distinct.

Communication evidence carries exact authorized text span or a permitted structured reference, independent artifact/test IDs, rater/method, quality anchor and confidence. Use `OBSERVED`, `NOT_OBSERVED`, `NOT_APPLICABLE`, `INSUFFICIENT_EVIDENCE` as explicit states. No observation is not zero quality; an observed counterexample can be anchor 0. An unobserved phase cannot earn synthetic evidence. Consent limits override raw-text persistence: if no retention, keep only explicitly permitted minimized features, or abstain from later span-dependent assessment.

Append events; freeze an ordered hashed manifest at close; score against that manifest; correct via linked review/regrade records. Hashes detect alteration but do not secure local files against their owner. Trainer/memory consumes a reviewed consent-permitted snapshot; review status is not synonymous with mere closure. Store unreviewed receipt separately. A deletion operation removes in-scope private payloads and in-memory/temp copies where supported, leaves a minimal tombstone only if permitted, and invalidates unavailable evidence-dependent views. Do not promise reproducible plaintext replay after the user deletes the evidence. Export is a copy, with explicit sensitivity labels; deleting the primary does not erase externally retained copies.

## 7. Scoring proposal with strict status

**[SOURCE: §14A; rubric JSON; D-03/D-04/D-10]** Base is Technical 60 / Communication 40 as the current owner hypothesis. **Subweights and anchors are UNAPPROVED, fixture-only until reviewed.** Preserve `schema_kind=PROPOSAL_NOT_VALIDATED`, `rubric_version=tia-60-40-owner-hypothesis-v0.3`, and approval state. They cannot be described as employer validity or an approved production grading formula.

| Axis | Proposed subscale maxima |
|---|---|
| Technical 60 | T01 correctness 24; T02 model/algorithm understanding 13; T03 planning/coverage 10; T04 test/debug/repair 9; T05 efficiency/maintainability 4 |
| Communication 40 | C01 clarification 6; C02 plan/narration 7; C03 progress/evidence 7; C04 gap-to-action/request 9; C05 feedback-to-execution 7; C06 closure 4 |

**[PROPOSAL from source fixture]** Anchors: 0 observed ineffective/counterexample; 1 repeated prompting; 2 partial demonstration; 3 adequate without undue aid; 4 robust on novel comparable task. Score observed dimensions as `max_points × anchor / 4`, preserving provenance and assistance. Do not award anchor 4 merely from one familiar passing example. Exact thresholds and sufficiency remain configurable pending calibration.

Always expose test truth, unassisted and after-hint outcomes, technical/communication components, observed coverage, confidence, difficulty, hint state, formula version and dispute link. Unknown anchors stay null; display known subtotal/unassessed capacity and mark aggregates provisional rather than silently zeroing or normalizing selective observations. Application of NOT_APPLICABLE requires a predeclared rule; otherwise the full total remains unresolved. Fluent explanation cannot overwrite T01 failure; technical success cannot automatically fill C01–C06.

**[SOURCE: changed from Rapid]** `extra_mentality_bonus.enabled=false`, hypothesis range `[10,15]`, positive-only, `RESEARCH_PENDING`. In the current design show narrative observable recovery and `NOT_ENABLED`, value null. No total above 100 is generated by default, no old +10 cap, and no assumption that 15 is an approved entitlement. Any future research variant requires an explicit separate policy/rater/fairness review. No mood, charm, inferred emotion, accent, disability, visa status or gratitude-only adjustment.

## 8. Real SQL target and resilience

**[SOURCE: FR-06/07; NFR-09; §§13,22]** Later M0 requires a real safe SQL evaluator: versioned synthetic/licensed first-order/tie/null, dedup/select, join-cardinality and clustered-failure cases with accepted alternatives. Initial execution is single-statement SELECT/CTE read-only; do not enable DELETE merely because a future question class mentions it. The Pandas match/replace example is a conceptual trainer fixture, not executable arbitrary Python.

**[PROPOSAL]** Use a reviewed parser plus SQLite authorizer/read-only defense, extension/file-attach prohibition, isolated ephemeral fixtures, strict statement/dialect support, host time/memory/result/event limits and killable worker. Regex alone is inadequate. Test malicious PRAGMA/ATTACH/multiple statements/extensions, long recursion and output floods. Compare semantics with declared ordering/null/type tolerances, not SQL text. A timeout/engine error is infrastructure uncertainty, not a proven wrong answer. No signed/hash receipt means no claimed executed test.

**[SOURCE / PROPOSAL implementation]** Prepare/commit/cancel avoids partial hint, model or result commits. Duplicate submit returns the same receipt or a consistent rejection; stale revision never commits. Crash restores the last valid revision with documented timer continuation; corrupt history fails safe. Preserve unsent local text within consent when a command fails. Show pending/denied/invalid/out-of-time/resumed/deleted/provider-unavailable states. Failure latency is instrumented separately from candidate pacing; model/network delays do not lower ability scores or secretly extend the clock.

**[SOURCE: NFR-02/NFR-05]** Determinism target: repeat same question/SQL/fixture at least 20 times on the target OS. Proposed local command p95 <300 ms excludes model calls and requires actual hardware, corpus, measured sample and explicit pass method. No latency claim is made now. Keyboard-only completion and status/contrast checks are required; voice remains future opt-in and no default affect grading.

## 9. Future work boundary and acceptance

**[PROPOSAL]** Sequence independent work as source/delta reconciliation → typed policy/context/communication contracts → reviewed registered HAL adapter and safe real SQL → complete offline user loop → score review/trainer/held-out retry → security/crash/accessibility/old-domain regressions. Preserve useful earlier tests and validate actual repository contracts before changing HAL core. Existing Witness/Research/Returns tests must pass on the implemented candidate revision; old prior passes do not prove a new domain works.

M1/future requirements remain visible: live provider (FR-15/16), Python isolation (17), adaptive history (18), full room UI (19), voice (20), additional formats (21), reminders (22), commerce (23), marketplace (24), and reviewed complexity judgment (26). They are neither implemented nor silently deleted from product scope. Model, voice, publication, payments and notifications need their respective later authorization; current planning does not request those actions.

`ACCEPTANCE_TEST_MATRIX_V3.csv` preserves prior cases with explicit new IDs and v3 requirement mappings, imports all 17 public UAT IDs, lists all 12 §28 hard-stop cases and 12 §28A cases, covers COM-FR-001–012 and exam:C01–C16, and supplies M0 positive/negative checks. `PRD28-HS-01..12` are **local identifiers for numbered prose cases**, not fabricated source IDs. Each row has expected result, provenance and `NOT_RUN`; no result is promoted from documentation inspection.

The matrix contains **202 planned cases**, including 84 rebased prior cases, 17 public UAT rows (12 also cover the exact §28A cases), 12 additional §28 hard-stop rows, 12 dedicated COM-FR rows, 16 examination rows, 34 explicit positive/negative cases for all 17 M0 FRs, and two explicit event-count/payload-size boundary scenarios for NFR-07. Every row specifies a failure condition, verification method and required evidence. Graph IDs use `graph:00/A01` through `graph:08/K12`; rubric and examination IDs have separate namespaces. Historical compatibility joins are marked as such; exact coverage uses the dedicated v3 rows rather than counting broad inherited mappings as implementation proof. Provider/voice/research checks have distinct later-stage labels.

| P0 requirement | Direct planned check | Observable verification target |
|---|---|---|
| COM-FR-001 | V3-COM-FR-001 | Material-turn count equals correctly attributed, privacy-permitted event count |
| COM-FR-002 | V3-COM-FR-002 | Clarification span/reply/action and B05 branch; no answer disclosure |
| COM-FR-003 | V3-COM-FR-003 | Plan narration links to actual edits/tests; fluent text cannot create test success |
| COM-FR-004 | V3-COM-FR-004 | Concept/recall/library/structural/unknown fixtures produce cited distinct gap labels |
| COM-FR-005 | V3-COM-FR-005 | Done/proved/unknown/next-test/request chronology, with separate C03/C04 and T04 |
| COM-FR-006 | V3-COM-FR-006 | Grant/deny/overlevel requests preserve atomic disclosure and assistance ledger |
| COM-FR-007 | V3-COM-FR-007 | Feedback→interpretation→action→test chain; aha-only produces no execution credit |
| COM-FR-008 | V3-COM-FR-008 | Submit/timeout/cancel summary matches frozen work; no invented completion |
| COM-FR-009 | V3-COM-FR-009 | Eleven tagged fixture subscales, evidence/unknowns, disabled bonus and reviewed-memory gate |
| COM-FR-010 | V3-COM-FR-010 | Evidence-backed speech-to-action drill followed by held-out matched retry |
| COM-FR-011 | V3-COM-FR-011 | Source/graph/prompt/host/event/rubric/trainer/test trace or explicit uncovered status |
| COM-FR-012 | V3-COM-FR-012 | Praise/keyword/empty-ask repetitions cannot increase outcome without changed evidence |

This establishes **planned test coverage**, not implemented prompt/host trace or verified candidate actions. CSV schema/ID/coverage inspection is an artifact check only. Actual application acceptance requires executing the listed procedures on the future implementation, retaining the required evidence and then recording PASS/FAIL with an actual result. All 202 rows remain `NOT_RUN`.

Keep `SPEC_COMPLETE`, `MVM_READY`, `M0_ENG_DONE`, `LIVE_UAT_DONE`, `USER_VALIDATED`, and `RELEASE_APPROVED` separate. This artifact does not claim any of those complete-product gates. Missing companion contracts/manual/source receipts remain explicit dependency gaps; owner hypotheses, rubric calibration, resource bounds and empirical transfer await evidence. Independent safe planning continues while these questions remain open.
