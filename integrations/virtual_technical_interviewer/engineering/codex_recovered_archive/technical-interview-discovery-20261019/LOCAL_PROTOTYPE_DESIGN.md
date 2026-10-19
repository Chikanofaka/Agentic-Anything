# Local prototype design — Technical Interview Best-Practice Lab

Date: 2026-10-19 · Status: **DESIGN ONLY; no runnable application or live agent demonstrated**.

## 1. Authority and limits

**[SOURCE]** The baseline is the canonical material in `repo/integrations/virtual_technical_interviewer/`: `粘贴的 Markdown (1)(6).md`, `index.html` (Atlas 00–08), `Technical_Interview_MVP_PRD_RAPID_v0.1.md`, and `00–08 逐图评审对话.pdf`, plus `repo/issue_register_v0_1.md`. The discovery checkout is pinned by the parent audit to `79656f5988bf861068052951d402fb6d8b2fd491`. The extracted `sources/atlas_data.json` and `sources/original_markdown_embedded.md` are working copies, not new product authorities. Source-line references below use the Markdown/Atlas numbering. This document reads the original text, Atlas metadata, rapid PRD, and issue register; PDF interpretation is handled by the parent audit and is not independently claimed here.

**[SOURCE: parent PDF audit]** Despite its filename, the supplied PDF is a nine-page export of Atlas diagrams 00–08 marked `DRAFT FOR REVIEW`, not the original review-dialogue transcript. Its hash matches the specified repository artifact. It therefore does not independently establish the missing F03/F04/F05/F06 review decisions. The parent audit retains extracted text and page renders under `receipts/`.

**[USER-APPROVED]** F01-001 corrects B05: **requirements unclear = YES → B06 clarification → B07 permitted reply → B05 recheck; NO → B08 ability assessment**. The original diagram remains an artifact to correct later; its inverted labels must not drive runtime behavior.

**[SOURCE]** F01-002 and F02-001 establish walkthrough omissions, not approved graph topology changes. F02-002 is a proposed edge-to-rule/document mapping awaiting review. The PRD references F03-001, F04-001, F05-001, and F06-002, which are absent from the available register; their contents and approval states remain unresolved. Do not invent them. Existing PRD behavior can be prototyped with its own provenance while these IDs remain unresolved.

**[ENGINEERING PROPOSAL]** Everything describing a data schema, implementation boundary, adapter, arithmetic rule, or acceptance procedure below is a proposal. No prior interviewer PRD, earlier employer research, personality theory, or assumed HAL plugin convention supplies requirements. No API, deployment, public commit, repository-core change, browser research, arbitrary Python execution, or voice/emotion analysis belongs to this prototype design.

## 2. Proposed local experience and delivery boundary

**[SOURCE: FR01–FR10; A01–A10; B01–B27; J01–J12]** Demonstrate one closed interview, an evidence-backed review, a targeted drill, and a second interview with honest comparison. Communication must be examined throughout, independently of technical outcomes. The interviewer may remain silent, question, challenge, provide permitted information, refuse help, or end on time. The Trainer acts after the interview closes.

**[ENGINEERING PROPOSAL]** Begin with a local terminal interface and local files. A later browser view may consume the same redacted host API; a single HTML file containing hidden answers is not an adequate disclosure boundary. No network connection or model is needed. A visible mode label accompanies every screen/export:

| Adapter | What actually happens | Required label |
|---|---|---|
| Scenario replay | Pre-authored candidate/interviewer turns and outcomes exercise declarative transitions | `SIMULATED — SCRIPTED SCENARIO; no live model; no candidate execution` |
| Manual session | Human supplies candidate text; an operator selects an allowed reaction and records judgments with evidence | `MANUAL — HUMAN-ANNOTATED; no live model; code not executed` |
| Optional later SQL verifier | Restricted SQL actually executes against isolated fixtures after its security tests pass | `EXECUTED SQL` only on the resulting test records; conversation adapter remains labelled separately |

Scripted expected results cannot be labelled executed tests, and scenario fixture success cannot establish a candidate's ability. A manual semantic judgment remains an attributed judgment, not a deterministic fact. The design does not assume a language classifier can understand free text.

**[ENGINEERING PROPOSAL]** Use one small SQL/data-transformation problem family: include all configured entities, including those with no matching facts; preserve required output grain; define null, ordering, and numeric rules explicitly. Prepare variant A and B with different data and wording and the same declared skills. A known passing alternative must be accepted on semantics and constraints, not text equality with a reference query. Initially store SQL as text and replay supplied outcomes. This validates control flow only. Real candidate execution and security validation are a later work package.

## 3. Two-session walkthrough

**[ENGINEERING PROPOSAL; FR01–FR08]** The deterministic scenario pack includes the following complete path, plus branch fixtures in the matrix:

1. **Prepare A:** Trainer chooses one observable target, such as explaining a failed result and acting on feedback. Freeze question, time budget, aid/disclosure policy, graph version, rubric version, scenario version, and adapter. The candidate sees the question and applicable rules, not the reference solution, hidden fixtures, or Trainer's private diagnostic notes.
2. **Greet/brief → clarify:** Candidate restates inputs, output grain, constraints, and assumptions. Exercise corrected B05 until the requirements are clear. As a configurable engineering proposal, factual task clarification is distinct from a charged solution hint; its accounting must be declared by policy and is not an approved universal rule. Clarification cannot silently leak the algorithm.
3. **Plan → implement:** Candidate states a bounded plan, tradeoffs, a next step and expected result, then provides the corresponding code artifact and progress explanation. A valid independent path may finish without any hint.
4. **First failure and response:** The scenario supplies a result where absent entities were lost. Candidate contrasts proven output with the unresolved gap. Interviewer chooses an allowed diagnostic question. Candidate paraphrases its meaning but cannot yet execute; record understanding separately from progress.
5. **Second feedback round:** Candidate narrows the gap to syntax or structural reasoning, states an independent next step, and requests a specific permitted resource when needed. Scenario A uses a refusal; candidate preserves valid work, proposes a smaller independent step, and retries or closes at expiry. A companion fixture grants a limited nudge. Neither action implies the other will occur in real interviews.
6. **Test/close A:** Preserve each attempt and passing subsolution. Candidate states completed work, evidence, remaining risks, and next step. Time expiry closes rather than extending itself. Commit the evidence snapshot before scoring or Trainer handoff.
7. **Review/drill:** Show technical evidence and communication evidence in separate columns with source events, assistance, quality, confidence, and missingness. Trainer chooses one evidenced weakness and a drill with measurable success: e.g. explain output-grain loss, propose a fix, and demonstrate it on a small permitted fixture. The drill is practice, not an extension of A's interview score.
8. **Interview B → compare:** Begin a new session with a variant, fresh event IDs, and declared policy/rubric. Measure the selected behavior again, including whether feedback led to a new action. Display raw before/after evidence and assistance. If evidence, difficulty, or assistance differs materially, mark comparison `not_comparable` or `limited_comparability`; never invent improvement. Two sessions demonstrate a loop, not transfer validity.

## 4. Declarative decisions and role authority

**[ENGINEERING PROPOSAL; FR02, FR03, FR07, FR09; F02-002 pending]** Store each rule as data: `rule_id`, `graph_node_ids`, `source_refs`, `authority_tag`, `from_state`, `trigger`, `guards`, `permitted_actions`, `transition`, `disclosure_ids`, `required_evidence`, `stop_condition`, and `policy_version`. Derived edge IDs use an explicit `PROPOSED:` prefix until source edges are mapped; do not fabricate original Atlas edge identifiers. Multiple matching rules require an explicit recorded operator/scenario choice; zero matches must produce a reviewable unsupported-state result, not an improvised transition.

| Decision | Required distinction | Permitted outcome / evidence |
|---|---|---|
| B05, B06, B07, B08 | Requirements unclear vs clear | Corrected clarification/recheck or ability assessment; log the answer and branch |
| C03–C15 | Correct; near-correct; unusual valid/slower; fundamentally mistaken | Neutral continuation, probe, tradeoff question, permitted nudge, or independent diagnosis; no forced canonical solution |
| C16–C18, D02–D09 | Claimed understanding; demonstrated understanding; executable knowledge; action; validated progress | Separate events and judgments; “aha” cannot set progress=true |
| C19–C22, D12–D19 | Request; permission; actual resource use; refusal; repeated blockage | Policy-specific scope and aid event; a second blockage returns to diagnosis/time check |
| E09–E17, F07–F15 | Syntax/local issue vs data/semantic/structural issue | Local testable patch or replanning; retain validated earlier artifacts |
| F02–F04, F16–F21 | All declared checks pass vs partial pass vs not executed | Honest completion status; no 4/20, 80%, or 20% universal thresholds |
| H01–H15, J08–J12 | Closed evidence; score; training; new session | Commit before handoff; score version and drill linkage preserved |
| K01–K12 | Current Plan 1 vs change proposal | Record proposed diff/evidence/test; manual adoption into a new version only |

**[SOURCE: original lines 15, 37–39, 51, 151; PRD §§2–4]** Professional requests are evaluated under the session policy. Politeness, persuasion, or urgency cannot authorize a forbidden answer. Silence is a selectable interviewer action; it is not approval, rejection, correctness, or candidate failure. A refusal is not itself evidence of poor candidate communication.

**[ENGINEERING PROPOSAL]** The host owns time, state, identity, permissions, fixture results, and scoring arithmetic. The interviewer adapter can propose only permitted actions and authorized disclosure IDs. A public response is rendered from an allowlisted content block after permission checking; a vague “no answer leak” instruction alone is inadequate. The candidate cannot self-author a grant, modify hidden fixtures, backdate actions, or issue a Trainer handoff. A Trainer receives committed evidence and explicitly releasable teaching material only after closure. Post-interview review does not automatically release every answer or the next session's secrets.

## 5. Communication examination in every phase

**[SOURCE: FR05; B04, B09–B17, B23; D02–D19; E05–E17; H06; PRD §2]** Technical success and communication quality are independent observations. Brief and accurate communication can be strong; verbosity, confidence of voice, charisma, mood, accent, introversion, extroversion, and inferred emotion are not scoring inputs.

**[ENGINEERING PROPOSAL]** Create a communication assessment slot for every phase reached and retain explicit missing/non-applicable states for phases or opportunities not reached. Do not force an invented utterance or unnecessary hint request just to fill a slot.

| Phase | Observable communication | Separate technical evidence |
|---|---|---|
| Prepare/greet/brief | Confirm relevant rules and raise a real ambiguity | No presumed technical capability |
| Clarification | Restate output/constraints and ask a bounded question | Correctness of requirement interpretation |
| Planning | Explain approach, assumptions, tradeoffs, next step | Feasibility, conceptual correctness, complexity |
| Implementation | Explain purpose and expected effect of a block; update progress | Actual artifact and intermediate result |
| Blockage/diagnosis | State what is done, proven, missing/risky, and proposed next | Root-cause reasoning and surviving subsolution |
| Resource request | Specify needed help and purpose; respect refusal/permission | Independent versus assisted contribution |
| Feedback/retry | Explain interpretation and changed plan; follow through | Action artifact and resulting validation, separately from understanding |
| Final validation | Describe differences between successes and failures; limits | Actual test report, scope of tested requirements |
| Closure | Concise honest recap, tradeoffs, unfinished work and next step | Final technical completion status |
| Review/drill | Discuss evidence and define a measurable practice action | Training-only evidence; cannot rewrite closed interview scores |

## 6. Evidence and reproducible scoring contracts

**[ENGINEERING PROPOSAL; FR04–FR09]** Minimal records:

- `Session`: IDs and versions; adapter; candidate-visible rules; separate aid permissions for documentation, web and AI; authoritative start/expiry; state; fixture hash; source manifest hash; prior-session reference.
- `TurnEvent`: immutable ID, contiguous sequence, actor/action, phase, source node IDs, proposed/original edge ID, timestamp, text/artifact reference, rule ID, permission/disclosure reference, assistance level, source kind (`candidate_input`, `manual_annotation`, `scenario_script`, `executed_verifier`), and adapter label.
- `Evidence`: ID, event references, skill/phase, `observed` (`true`, `false`, `not_applicable`, `insufficient_evidence`), separate `quality` (`0..4` or null), confidence (`low/medium/high` or null), independent/assisted status, assessor, method, explanation, and source/rubric version. `observed=false` means not observed within a defined opportunity, never quality=0. `observed=true, quality=0` requires actual evidence of poor behavior. Missing capture becomes `insufficient_evidence`; no opportunity becomes `not_applicable` with reason.
- `Attempt/TestReport`: immutable code/data hashes, parent attempt, test-set version, actual or scripted result kind, per-case outcomes, errors, artifact references, and visibility policy. A scripted result has no execution duration or fabricated verifier receipt.
- `Scorecard`: separate `technical_base`, `communication_base`, `base_total`, `bonus`, `illustrative_total`; known subtotals, unassessed maximum/coverage, unscorable flags, evidence breakdown, calculation version, and source provenance.
- `TrainerPlan`: evidence-linked priority, rationale, drill, success criterion, expected observation opportunities, and second-session link. A claim of improvement needs evidence from both sessions.

**[ENGINEERING PROPOSAL]** Append new events; correct an annotation with a superseding record, never in-place edits. Freeze a closing manifest with hashes of ordered events and artifacts, then compute a versioned score snapshot from that manifest. Reject duplicate IDs, missing references, sequence gaps, unauthorized actors, and replay mutations. Hashes can detect accidental changes; local files alone do not provide adversarially secure immutability against the machine owner. A regrade creates a new score version linked to the unchanged evidence; replay of a frozen version reproduces the same decisions and arithmetic.

**[SOURCE: PRD §5; original lines 165–169]** Current Plan 1 is **Technical 60 + Communication 40 = base 100**, configurable and labelled a training hypothesis, not an employer norm. Edge-case foresight is within Technical. The suggested approximately 20% of Technical is not a fixed requirement. Optional positive bonus is **0 to +10**, separate from the base; older 10–15% and mixed historical weights must not enter current arithmetic.

**[ENGINEERING PROPOSAL]** Before session start, configure criterion weights summing to 60 and 40. Human-anchored quality uses an explicit 0–4 scale; fully assessed criterion points equal `criterion_weight × quality / 4`. Score independently solved and assisted evidence separately in the breakdown; do not invent a universal hint penalty. Select anchors and optional assistance adjustments in a versioned rubric before the session. A technical defect cannot directly reduce Communication; a clear explanation cannot manufacture technical correctness.

Unknown quality remains null. Report known earned subtotal plus unassessed maximum; do not silently treat unknown as zero or normalize it into a full score. If an applicable criterion is unresolved, its domain total and the base total remain provisional/null. A `not_applicable` slot needs a predeclared rubric applicability rule; the prototype must not redistribute its points ad hoc. If that rule is missing, leave the total provisional. Publish raw evidence and coverage even when no defensible total is available.

Bonus is opt-in and non-deductive. An enabled bonus requires event-backed recovery/professional conduct criteria, including concrete diagnosis and a constructive next action; charisma, emotional interpretation, thanks alone, or an “aha” earns no automatic bonus. Insufficient evidence leaves bonus `null` with status, not an invented 0 or 10. Disabled bonus displays 0 with `disabled`. When complete, `illustrative_total = base_total + bonus` may be up to 110 and is explicitly labelled illustrative. The same event may support different documented behaviors, but a single base-scored behavior cannot receive duplicated bonus credit without an explicit reviewed rubric rule.

## 7. Local safety and execution staging

**[ENGINEERING PROPOSAL]** Stage A stores and displays text and uses fixture/manual outcomes; it executes neither candidate SQL nor Python. Escape text in any later HTML rendering. Store artifacts under a dedicated local run directory; reject path traversal and prevent candidate-facing export of hidden inputs, expected answers, permission internals, or future questions. Use synthetic data, no credentials, telemetry, or automatic external uploads.

**[ENGINEERING PROPOSAL]** Stage B may add a restricted SQLite verifier after review: isolated ephemeral database from trusted fixtures, read-only single-statement SELECT/CTE capability, SQL authorizer plus query-only mode, extensions disabled, ATTACH/DETACH and file/network access forbidden, bounded result size, deterministic comparison and ordering rules, host-enforced time/resource limits, and a killable worker. Do not rely on regex filtering or `query_only` alone as isolation. SQL dialect and fixture semantics must be explicit. Arbitrary Python remains unsupported. These controls are proposed requirements, not verified properties of a shipped sandbox.

**[ENGINEERING PROPOSAL]** A real provider, autonomous semantic evaluation, voice capture, browser aid, public release, and HAL integration are separate work packages. The repository audit must establish actual extension entrypoints before any domain registration or `AGENTS.md` / `identity.md` / `soul.md` scaffolding. This design does not claim that creating a directory registers a Type B application.

## 8. Acceptance and next decisions

**[ENGINEERING PROPOSAL]** `ACCEPTANCE_TEST_MATRIX.csv` defines future checks; all rows start `NOT_RUN`. A document inspection, schema check, or passing scripted fixture is evidence only for its stated layer, not for a working live interview or market validity. Record command/procedure, actual result, artifact, version, and date before changing a row to PASS or FAIL. The first implementation increment should exercise B05, two complete reaction rounds, understood-without-action, repeat blockage, denial, partial progress, all-phase communication coverage, score separation, and post-close handoff in one deterministic replay.

**[RESEARCH PENDING]** Obtain or reconcile the absent issue IDs; calibrate criterion anchors and per-dimension weights; define opportunity/applicability rules and assistance adjustments; decide optional bonus behavior and avoid duplicate credit; validate paired-question comparability; review the permitted disclosure catalog and SQL boundary. These do not block writing a local fixture-driven proposal, but they block claims of a finalized employer rubric, validated transfer, or production readiness.
