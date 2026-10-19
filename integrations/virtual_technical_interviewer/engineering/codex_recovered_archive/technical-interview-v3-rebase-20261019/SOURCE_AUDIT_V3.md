# Source audit — full v3 baseline rebase

**Date:** 2026-10-19 (Asia/Shanghai). **Requirements snapshot:** `53188034400be6c534d2ded56a9386ea55d6ad0e`, `integrations/virtual_technical_interviewer/TIA_FULL_PRD_v3`. **Work scope:** requirements/document reconciliation only. The earlier discovery files are preserved unchanged. No application, agent prompt, runtime policy, live provider, publication or repository mutation is performed by this audit.

The user-designated full v3 package is now the requirements reference. Rapid v0.1 and prior maps are antecedents used to preserve compatible work, not active requirement authority. The v3 source hierarchy still distinguishes original intent, explicit later decisions, verified review records, draft Atlas and proposals. A tag inside a document is not proof of an empirical claim or an independently available approval transcript. The current instruction to rebase documents governs over the bundled engineering delta's request to implement a vertical slice.

## Baseline actually read and checked

The full **895-line** [v3 PRD](sources/TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md) was read, including §§00–32 and appendices. The communication matrix, source trace, decisions, rubric JSON, UAT inventory, engineering delta, README and manifest were also read completely. The archived Rapid note was previously read completely and is used only to identify superseded guidance.

| Artifact | Actual coverage and authority | Limits |
|---|---|---|
| `TIA_FULL_BASELINE_PRD_v3.md` | 895 lines; current requirements target; SHA-256 `620c7c313d248a9e1bc43a220c8ab79c82e743cb5d3269ebe6150e476d5e2fb4` | Explicit hypotheses, proposals and NOT_RUN remain so. This is not implementation evidence. |
| `COMMUNICATION_EXAMINATION_MATRIX.csv` | 16 observation rows, source lines 2–17 | Observation IDs C01–C16 are distinct from six rubric axes and Atlas C nodes. Point-context column is not an additive rubric. |
| `TRACEABILITY_SOURCE_TO_REQUIREMENT.csv` | 18 source/review trace rows, lines 2–19 | Several target aliases are undefined or ambiguous; corrected mappings below are proposals. |
| `DECISION_REGISTER.md` | 13 decisions D-01–D-13, lines 5–17 | Statements of current baseline, rejected assumptions and open gates; original historic review records are a separate source. |
| `RUBRIC_60_40_PROPOSAL.json` | Five Technical and six Communication subscales, anchor model, disabled bonus | Top-level 60/40 is the current user hypothesis; subweights and anchors remain unapproved. |
| `UAT_MATRIX_v3.csv` | 12 C-UAT and 5 INT-UAT scenarios, lines 2–18 | All 17 supplied scenarios are NOT_RUN. |
| README / engineering delta | Reconcile useful prior work, preserve source hierarchy and gates | No implementation, external write or paid call is authorized merely by reading these files. |
| `SHA256_MANIFEST.json` | Eight locally present listed text artifacts match their package hashes | Manifest also lists DOCX/PDF; those renderings were not downloaded or inspected. PDF manifest size is 565,250 bytes, but verified Git tree size is 590,385 bytes: package integrity discrepancy remains open. Rapid and manifest itself are Git-blob verified, not self-listed. |
| Prior secure original and Atlas | Original 229 logical lines and all 166 Atlas nodes/226 SVG edge elements were read during the preserved audit; original equals embedded source lines; current task supplies unchanged-blob continuity | Private text is referenced by logical line number only. No full transcript or personal quotation is copied into these outputs. Atlas remains a draft, not a runtime contract. |
| Prior `issue_register_v0_1.md` | Four actual entries: F01-001, F01-002, F02-001, F02-002 | Current v3 descriptions do not create unavailable historic records. |

[Source verification receipt](receipts/source_verification.json) records Git-blob verification for all ten fetched text artifacts. This audit independently recomputed hashes of the eight locally available files listed in the package manifest; all matched. A match establishes file identity, not correctness, approval or engineering acceptance. In particular, the eight matching text artifacts do **not** establish full-package integrity: `SHA256_MANIFEST.json` lines 42–44 records the PDF as 565,250 bytes, while [remote Git-tree receipt](receipts/remote_manifest.json) records 590,385 bytes at blob `67f6486b5d91c7238937516fb1717023fe1444e3`. PDF/DOCX content and equivalence were not read or verified; the known PDF size disagreement must be reconciled before claiming a consistent full package.

The v3 references to `source_private/ORIGINAL_USER_VOICE_TRANSCRIPT_VERBATIM.md`, `contracts/DOMAIN_AND_DATA_CONTRACTS.md`, `tests/UAT_MATRIX.csv`, `engineering/CODEX_MASTER_COMMAND.md`, historic methodology files and `status/HUMAN_GATE.md` do not establish that those companions are present in this ten-text-file package. Private original provenance is available through the prior secure audit; the exact named private companion is absent from the v3 pack. The package manifest does not list its checksum despite PRD §32 referring to one. The supplied `UAT_MATRIX_v3.csv` is a real attachment; it must not silently be treated as the nonexistent `tests/UAT_MATRIX.csv` without an explicit alias/expansion decision. Architecture work may separately resolve repository-owned contracts; this audit does not mark them verified merely because the PRD names them.

## Requirement coverage and namespaces

[REBASED_SOURCE_TRACEABILITY.csv](REBASED_SOURCE_TRACEABILITY.csv) has **144 rows**:

| Row kind | Count | Coverage |
|---|---:|---|
| Functional requirements | 28 | `v3:FR-01`–`v3:FR-28`, exact PRD register lines 387–414 |
| Communication requirements | 12 | `v3:COM-FR-001`–`v3:COM-FR-012`, lines 423–434 |
| Communication observations | 16 | `observation:C01`–`observation:C16`, companion matrix lines 2–17 |
| Rubric subscales | 11 | `rubric:T01`–`rubric:T05` and `rubric:C01`–`rubric:C06`, PRD lines 341–352 |
| Bonus policy | 1 | `rubric:MENTALITY_BONUS`, disabled JSON policy |
| Nonfunctional targets | 12 | `v3:NFR-01`–`v3:NFR-12`, PRD lines 609–620 |
| Supplied source-trace reconciliation | 18 | `source-trace:SRC-001`–014 and R-001–004 |
| Prior-row reconciliation | 36 | All prior MAP-001–022 and CM01–14, each retained in `legacy:` namespace |
| Workflow contracts | 10 | `workflow:W01`–W10, PRD lines 464–473 |

The actual register has **28 FRs**, not 36. The extra communication requirements use **COM-FR**, not an invented COMM-FR prefix. Previous Rapid `FR01`–`FR10` must never be joined to current `FR-01`–`FR-10` by removing punctuation: their meanings differ. For example, old FR05 meant cross-phase Communication examination; current FR-05 means structured candidate actions, and the communication contract now expands into twelve COM-FR requirements.

| Identifier | Exact namespace and meaning | Collision to avoid |
|---|---|---|
| `rubric:C02` | Explainable plan/in-flight narration, proposed maximum 7 | Not observation C02 clarification; not Atlas C02 correctness inspection. |
| `observation:C02` | Clarification observation from matrix row 3 | It maps provisionally to `rubric:C01`, not `rubric:C02`. |
| `graph:02/C02` | Existing Atlas interviewer correctness/feasibility/complexity/edge inspection | A graph state is not a score dimension or observation ID. |
| `observation:C15` / C16 | Post-session training review/transfer | They do not add two extra interview-score dimensions or revise a locked score. |
| `workflow:W01` | Intake contract | Separate from workstream W1 and any release gate. |
| `decision:D-02` | Current decision register's P0 Communication priority | Separate from `graph:03/D02`, the candidate feedback restatement node, and untyped `D02` source aliases. |
| `legacy:CM02` | Prior engineering observation phase | Separate from both v3 observation and scoring C IDs. |

The acceptance matrix uses `exam:C01`–C16 for the same supplied observation rows. This is an explicit namespace alias to this file's `observation:C01`–C16, not a rubric join. The source package provides no complete authoritative observation-to-six-axis crosswalk. Our many-to-many observation/scorer links are **engineering proposals** and are labeled accordingly. The matrix's fourteen numeric point-context cells sum **99**; summing them into a score would be an error. Only the six proposed scorer maxima sum 40.

## Communication → agent → host → scorer → trainer mapping

The CSV now supplies `agent_contract_refs`, `host_enforcement`, `trainer_tags`, and `agent_host_trainer_mapping_status` for **all 12 COM-FR rows, all 16 observation rows, and all 11 rubric subscale rows**. Eighty rows in total have these proposed links. Agent paths follow the PRD §18A examples; clause names/tags are newly proposed engineering references. **No referenced agent/config file was created or verified executable in this rebase.** Prompt prose is not an authorization boundary.

| Communication contract | Proposed agent-contract responsibility | Host rule / evidence boundary | Proposed trainer focus |
|---|---|---|---|
| COM-FR-001 | Interviewer AGENTS typed event protocol; consented candidate preferences | Host actor/phase/sequence/timestamp and linked artifacts; authorized capture only | Coverage and faithful observation |
| COM-FR-002 | Interviewer identity clarification; soul answer secrecy; policy B05 | Approved B05 semantics and authorized fact projection | Clarification and requirement alignment |
| COM-FR-003 | Plan/checkpoint prompts and artifact linkage | Match explanation to actual revisions/tests; prose never changes PASS | Plan narration connected to code |
| COM-FR-004 | Gap taxonomy with provisional classification | Separate concept, syntax/library and structural uncertainty; allow abstention | Diagnose the smallest evidenced gap |
| COM-FR-005 | Verified-work/recovery narrative | Done/proved/unknown/next-test/request chronology; T04 remains independent | Evidence narrative and bounded replan |
| COM-FR-006 | Policy-aware collaboration and hint proposal | Atomic grant/deny, aid ceiling, secrecy and assistance ledger | Precise permitted help and policy compliance |
| COM-FR-007 | Feedback-to-action observation | Link cue to plan/code/diagnostic action and result; acknowledgment is not progress | Autonomous follow-through |
| COM-FR-008 | Honest professional close | Freeze true completion boundary and host deadline; no gratitude-based correctness | Concise synthesis and calibrated limits |
| COM-FR-009 | Versioned rubric and observer-only model role | Host arithmetic, missingness, confidence, separate outputs; bonus disabled | Score evidence and calibration |
| COM-FR-010 | Post-lock trainer identity and training contract | Read-only reviewed packet, consent, immutable old score, comparable held-out retry | Communication drill and transfer |
| COM-FR-011 | Source/graph/policy/persona/rubric/trainer references | Resolve namespaced IDs and versions; unknown policy cannot execute | Traceable correction of rules |
| COM-FR-012 | Semantic evidence and anti-keyword criteria | No uplift from repeated empty asks/keywords without new verifiable action | Unscripted feedback-to-action |

The trace references **145 of 166 Atlas nodes**. This is useful conceptual coverage, not proof that 145 executable policies are complete. The remaining draft nodes are explicitly **unmapped** in this CSV:

`graph:00/A01`, `graph:00/A02`, `graph:00/A03`, `graph:00/A04`, `graph:00/A05`, `graph:00/A06`, `graph:00/A07`, `graph:00/A08`, `graph:00/A13`, `graph:01/B17`, `graph:01/B27`, `graph:02/C01`, `graph:02/C15`, `graph:02/C23`, `graph:03/D07`, `graph:03/D16`, `graph:04/E01`, `graph:05/F17`, `graph:05/F18`, `graph:05/F21`, `graph:07/J01`.

The classification and freeze impact below prevent the numerical 145/166 count from being mistaken for P0 completion. None of these 21 is classified as exclusively future scope merely to avoid coverage.

| Unmapped node(s) | Classification / why not directly mapped | Effect on executable-flow freeze |
|---|---|---|
| graph:00/A01 | Strategic research start; v3 §§00/05/27A retain research intent | Does not block a bounded runtime by itself; does block claiming validated optimal interview behavior without research. |
| graph:00/A02 | M0 overview of question/rules/time; detailed targets are FR-01/02/03 | Needs an explicit aggregation/alias to detailed intake/brief contracts, not duplicate runtime state or score. |
| graph:00/A03, A04, A05, A06 | P0 Communication/interaction overview; detailed behavior is COM-FR-001/003/007 and FR-08 | Freeze requires explicit alias/coverage from these summaries to detailed turn contracts; counting overview nodes as additional events would be wrong. |
| graph:00/A07, A08 | P0 testing/evidence/scoring overview; FR-07/10 and COM-FR-005/009 | Require a documented aggregation of test/recovery/scoring paths; do not create extra score categories from the overview. |
| graph:00/A13 | M0 session closure overview | Needs alias to host close/receipt/trainer boundary. A summary node does not prove a terminal state is enforced. |
| graph:01/B17 | P0 local diagnosis, repair or question; precise standalone contract absent | Must map to COM-FR-004/005 and FR-08 with observable gap/action and retry/stop guards before freezing local-blockage flow. |
| graph:01/B27 | M0 end/next-session entry; cross-session transition not expanded here | Must define end versus explicit new session and reset conditions under FR-04/12/18; do not automatically restart an interview. |
| graph:02/C01 | P0 receipt of candidate plan/code/explanation; input boundary not singled out | Needs COM-FR-001/003 and FR-05/08 actor/artifact/phase validation before freezing interviewer turn intake. |
| graph:02/C15 | P0-relevant **HYPOTHESIS** about independent diagnosis/redefining subproblem | Conditional policy proposal under FR-08 and COM-FR-005; no automatic help right. Freeze requires approved allowed-action conditions, not promotion of the hypothesis. |
| graph:02/C23 | P0 observations transferred to evaluation | Needs FR-10 / COM-FR-009 evidence-commit/assessor rules; model observations must not become authoritative test facts. |
| graph:03/D07 | P0 independent combination/small attempt after uncertain recall | Needs COM-FR-004/007 actual attempt/result links. Freeze cannot infer success from proposing a combination. |
| graph:03/D16 | P0-relevant assistance acknowledgment; not an independent scored gratitude requirement | Map to event/help provenance (COM-FR-001/006) or explicitly declare non-scoring behavior. Interim gratitude is not automatically C06 closure or bonus evidence. |
| graph:04/E01 | M0 question-to-candidate-solution entry | Needs FR-05 / COM-FR-002/003 transition to scoped plan. May alias detailed states once explicit; no forced candidate solution claim. |
| graph:05/F17 | P0 decision whether diagnostic guidance is permitted; source HYPOTHESIS | FR-09 / COM-FR-006 must enforce permission, time and disclosure ceiling; omission blocks frozen recovery-help policy. |
| graph:05/F18 | P0 authorized continuation of repair | Needs FR-04/07/09 and COM-FR-005/007 retry guards, remaining time and new evidence; permission is not technical progress. |
| graph:05/F21 | M0 question termination/next-question transition | Needs host terminal reason and next-question policy under FR-04/12; omission blocks exact termination/re-entry specification. |
| graph:07/J01 | M0 training-cycle start | Needs FR-12/18 consented history and explicit initiation rule; cannot assume scheduling or autonomous restart authorization. |

These gaps prevent claiming a **frozen, fully executable P0 flow**. They do not block this completed document rebase or safe proposed design. The rows identify exact existing v3 target requirements without claiming the missing executable contracts have been created.

Some unmapped nodes are overview/re-entry nodes and some carry local actions; they are not declared “non-P0” merely to claim coverage. COM-FR-011 permits uncovered items to be flagged. A later reviewed policy expansion must decide which need their own executable contract or an explicit alias. The PRD example `decision_node="03-COM-GAP"` at line 501 is a **proposed event-schema identifier**, not an existing Atlas node. It must never be reported as verified graph provenance.

## Current scoring: retain 60/40, revise the old proposal carefully

- **Current baseline hypothesis:** Technical 60 and Communication 40, separate evidence and outputs (PRD lines 324–364; decisions D-03/D-10). Not employer weights, hiring probability or market validation.
- **Specified but unapproved subweights:** Technical 24/13/10/9/4; Communication 6/7/7/9/7/4. Their sums are 60 and 40. The 0–4 anchor model and `max_points × anchor/4` calculation are engineering proposals.
- **Missingness:** NOT_OBSERVED is distinct from observed counterexample/zero. Show coverage, confidence and provisional sums; do not turn selectively observed evidence into false full-scale certainty. Presence, quality and observation opportunity remain separate considerations.
- **Technical/Communication independence:** a compelling explanation cannot repair failed test results. A successful test does not manufacture communication evidence. Feedback integration requires actual linked plan/code/diagnostic action, with help provenance preserved.
- **Bonus:** v3 JSON says `extra_mentality_bonus.enabled=false`; the 10–15 hypothesis is a separate, positive-only unapproved research variant. The old Rapid optional cap +10 is archival and **superseded as active policy**. Do not enable a 10-point award simply because earlier prototype design mentioned it; do not assume v3's hypothetical upper limit 15 authorizes any award.
- **No old four-factor fallback:** 40/20/25/15 is explicitly rejected as the active baseline. Its reappearance in Q07 is a stale internal question, not permission to revive it.

## Review records: present records versus v3 attestations

| Review ID | Independent available evidence | Meaning/status retained |
|---|---|---|
| F01-001 | Prior issue register line 7; v3 PRD line 197; D-09 line 13 | B05 YES→clarify/recheck; NO→ability. User accepted; original Atlas not edited. |
| F01-002 | Prior register line 10; v3 line 197 | Walkthrough coverage correction across execution/testing/termination. Not evidence of absent nodes or approved graph rewrite. |
| F02-001 | Prior register line 11; v3 line 197 | Full second-turn explanation and understanding/action/progress distinction. Graph sufficiency review remains separate. |
| F02-002 | Prior register line 12 | Requirement candidate for graph-to-policy mapping, not approved final architecture. Current v3 makes mapping work explicit without inventing historical approval. |
| F03-001 / F06-001 | v3 line 197 and supplied trace R-003 line 18 cite them | **Original review entries unavailable.** The current P0 requirement remains actionable from v3; its historical approval attribution is unverified. |
| F04-001 / F05-001 / F06-002 | Listed only by archived Rapid among the fetched requirements | Original records unavailable; do not silently carry them forward as active v3 issues. **F06-001 is not F06-002.** |

The earlier PDF named as a review conversation was inspected in the preserved audit and contains the nine-page draft Atlas, not the review transcript. It cannot fill these provenance gaps. The new v3 DOCX/PDF renderings have not been inspected here; no dialogue or approval is inferred from them.

## Material source inconsistencies and proposed handling

| Finding with exact source location | Handling in this rebase |
|---|---|
| PRD line 829 Q07 asks whether to retain an older four-factor alternative, conflicting with lines 24/326/337 and decision D-10 line 14 | Treat explicit current 60/40 and rejection as controlling; flag Q07 for source cleanup, leave source untouched. |
| §26 gates at lines 685–690 and §26A sequence at line 709 assign different meanings to G0–G5 | Namespace gates by section pending an agreed sequence. Do not report “G2 passed” without section and receipt. No gate advances from this document work. |
| Supplied trace SRC-001 line 2 uses undefined `F-ADMIN-01` and W01 for admin | Propose current FR-03/workflow W03 for briefing; W01 remains intake. Do not invent an FR definition or silently change source. |
| Source trace D00–D08 aliases overlap real Candidate graph D IDs; unqualified C IDs also overlap three namespaces | Use explicit diagram/node, scorer, observation and requirement namespaces. Preserve ambiguous raw source targets in trace notes. |
| Communication matrix `When_observed` is OPEN for its first 14 rows even when `Interview_Phase` is PLAN/RECOVER/CONCLUDE | Preserve raw value; use Interview_Phase for stage mapping. Meaning of OPEN is unresolved; never force all observations into the opening stage. |
| Matrix point-context total is 99 while scorer Communication totals 40 | Treat context as repeated links to dimension maxima, not 14 independent scoring awards. Many-to-many axis mapping remains proposed. |
| PRD line 501 references non-Atlas `03-COM-GAP` | Explicit proposed policy identifier; not an actual graph node. |
| PRD lines 416/743/786/810 refer to companion paths absent from the supplied text pack | Record source-artifact gaps; supplied 17-row UAT and expanded planned matrix are real artifacts, but not executed typed contracts. |
| PRD line 855 says private original SHA is in manifest, but package manifest omits private source | Rely on prior secure-source identity checks; do not claim the package manifest attests to a private file it does not list. No raw source copy added. |
| PRD line 887 says end of v2 master PRD inside v3 | Editorial residue; not a second active baseline or source reset. |
| Atlas B05 labels and H10 earlier weights remain old; scorecard SVG duplicates remain | Approved B05 semantics and v3 scoring control proposed implementation; raw graph remains preserved, physical edge IDs retained. 226 SVG elements represent 202 distinct diagram/title/label triples; repeated arrows never multiply points. |
| Prompt/file paths in §18A and architecture sections look concrete but are proposals | Trace labels them NOT_CREATED / ENGINEERING_PROPOSAL. Runtime enforcement cannot be inferred from path names. |

## No-loss reconciliation of previous 36 rows

Every old mapping row appears once under `legacy:` with a current target and disposition. Counts: **17 retain and extend**, **1 retain approved semantics** (MAP-004/B05), **3 retain 60/40/missingness while extending proposed formula** (MAP-013–015), **1 superseded active bonus policy** (MAP-016), and **14 retain behaviors while remapping observations** (CM01–CM14).

The 14 earlier communication phases are not discarded, but they do not become sixteen observation rows or six scoring axes by ID similarity. Planning/narration, feedback interpretation, precise help, refused help, repeated blockage, failure diagnosis, closing and post-session learning map many-to-many. Post-session review/training remain distinct scopes and cannot retroactively inflate the interview score. The prior minimal UI idea remains a subset; full room UI is M1 in v3, while no-key M0 onboarding/local flow remain necessary. The prior proposal did not authorize live provider/voice/spend, and v3 does not do so either.

## Planned acceptance linkage and actual verification

The expanded [ACCEPTANCE_TEST_MATRIX_V3.csv](ACCEPTANCE_TEST_MATRIX_V3.csv) is a planned acceptance inventory, separate from the supplied 17-row UAT attachment. Trace `acceptance_test_ids` links actual matrix IDs rather than repeating generic “add tests” gaps. Requirement joins use exact current FR/COM-FR identifiers; observation joins use the explicit observation↔exam namespace alias; rubric joins use scorer IDs. All 28 FR, 12 COM-FR, 16 observation and 11 subscale rows have concrete valid joins. Five additional NFR rows (NFR-01/07/10/11/12) link relevant existing tests through explicitly labeled `ENGINEERING_SEMANTIC_MAPPING`, not an exact NFR-ID source-reference join. NFR-07 additionally links two explicit positive/negative event-count and encoded-payload boundary scenarios, added during final cross-check. The matrix now has 202 planned cases. Cap values and counting/reserved-capacity mechanics remain proposed until implemented and tested. Test presence is not execution: all 200 current acceptance scenarios remain **NOT_RUN** until implemented fixtures and run receipts exist.

This audit's completed checks are limited to source/trace integrity: exact register coverage, distinct namespaces, all 36 prior rows represented, actual node/edge IDs, source line bounds, known review-line references, proposed agent/host/trainer links, manifest hashes and scoring arithmetic. Prior HAL/Witness regression receipts are carried forward only for their recorded scope. The earlier 84 interview acceptance cases were planned **NOT_RUN**, not executed prototype evidence; neither those cases nor old HAL receipts automatically establish v3 feature acceptance. No v3 app UAT, model run, rater study, market validation, user trial, release or paid provider activation is claimed.

## Completion and remaining work

The baseline rebase is complete as a document/trace task. Still open for future engineering are executable typed contracts, licensed question fixtures, reviewed host guards, actual agent files, scorer/observation calibration, full graph-runtime mapping, source inconsistency cleanup, unavailable historic review records, and recorded positive/negative UAT results. These do not justify inventing missing source or rewriting archived work. Current v3 P0 work can be designed while source provenance gaps stay visible.

The rebase creates only `REBASED_SOURCE_TRACEABILITY.csv` and this `SOURCE_AUDIT_V3.md` within the new isolated output root. No private transcript text or personal anecdote is reproduced in either. No original repo/source artifact is changed. Publishing these outputs is a separate action, not implied by their existence.
