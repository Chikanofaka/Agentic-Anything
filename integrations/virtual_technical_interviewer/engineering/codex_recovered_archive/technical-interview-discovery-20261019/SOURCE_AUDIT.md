# Source audit and P0 Communication observation proposal

Date: 2026-10-19 (Asia/Shanghai). Scope: isolated engineering discovery against the supplied Rapid PRD, original Markdown, Atlas and available review record. This is a source audit and operational proposal, not a final PRD, approved hiring rubric or proof of a working MVP. No previous Technical Interviewer Agent PRD, discovery response, historical handoff, external market research or inferred employer standard is a product authority here.

## 1. Baseline identity and completeness

[SOURCE] The authoritative repository snapshot provided for this audit is commit `79656f5988bf861068052951d402fb6d8b2fd491`. Repository download integrity and HAL findings are owned by the parent audit; this document independently checked the local source contents and their relationships.

| Source | Inspection and provenance | Status |
|---|---|---|
| [Original Markdown](repo/integrations/virtual_technical_interviewer/粘贴的%20Markdown%20(1)(6).md) | Read all 229 logical lines. Its `splitlines()` exactly equals all 229 `source_lines` in the Atlas DATA object and the extracted Markdown mirror. | Present; primary intent, containing proposals and uncertainty rather than validated universal practice. |
| [Atlas HTML](repo/integrations/virtual_technical_interviewer/index.html) | Read all 166 node labels, descriptions, status tags and source spans; parsed all SVG edge titles and labels across 00–08; inspected the complete executable UI script. Embedded DATA exactly equals `sources/atlas_data.json`. | Present; reviewed draft, not frozen best practice. |
| [Rapid PRD](repo/integrations/virtual_technical_interviewer/Technical_Interview_MVP_PRD_RAPID_v0.1.md) | Read all 88 lines. Lines 5–10 set source precedence; lines 77–88 authorize bounded isolated discovery/prototyping with stated limits. | Present; current working handoff, explicitly not final architecture or market validation. |
| [Issue register](repo/issue_register_v0_1.md) | Read all 19 lines. Four actual entries: F01-001, F01-002, F02-001, F02-002. | Present; specific approval/coverage/proposal statuses must be preserved. |
| [PDF named 00–08 逐图评审对话](repo/integrations/virtual_technical_interviewer/00–08%20逐图评审对话.pdf) | PDFKit extraction in [receipt](receipts/review_pdf_text.txt) identifies nine chart pages, 00–08, each marked `DRAFT FOR REVIEW`; parent visual inspection confirms an Atlas export. Text extraction does not expose the chart bodies, so it is not a substitute for HTML/source review. | The file is present but is a nine-page graph atlas, not the conversational review transcript its filename suggests. No approval is inferred from its name or presence. |

[SOURCE] The original standalone Markdown is present; the issue register is present. The incomplete part is the review history: the PRD references **F03-001, F04-001, F05-001 and F06-002** at line 8, but these entries are absent from the available register. The file called the review dialogue PDF does not supply the missing conversational decisions. Their contents, statuses and links to graph nodes remain **UNVERIFIED**. Do not invent what any of these IDs means.

[SOURCE] Atlas node statuses are 133 `SOURCE`, 25 `PROPOSED`, 4 `HYPOTHESIS`, and 4 `FUTURE`. `SOURCE` means the Atlas author connected a node to the original text; it does not prove user approval of its exact wording, empirical validity or executable completeness. The HTML detail panel shows at most seven truncated excerpts per node. This audit used the full original lines, not those display excerpts alone.

## 2. Approval and conflict ledger

| Item | Exact evidence | Current interpretation and limitation |
|---|---|---|
| B05 inverted branch labels | Original L15/L31/L47; Atlas `01/edge5` title `B05->B06`, HTML L299 has label `否`; `01/edge8` title `B05->B08`, L315 has label `是`; issue register L7; PRD L26/L38. | **[USER-APPROVED] F01-001:** YES means clarify, then recheck; NO means ability assessment. The original graph is still unchanged. The explicit gate was a review structural addition, not a verbatim source instruction. Apply the approved semantics in an isolated prototype and retain raw labels in trace records. |
| Diagram 01 coverage | Register L10, F01-002. | **[SOURCE] Established walkthrough correction:** explain execution, blockage, testing, retry and termination together. This is not evidence that those nodes were missing from the diagram. Revisit conditions on B18→B14 and B21→B22 without claiming an approved redesign. |
| Diagram 02 understanding vs action | Register L11, F02-001; C16 description at original L37–39; raw `C16->C17` label `是` at HTML L963; PRD L18/L29/L40. | **[SOURCE] Established walkthrough correction:** understanding, executable knowledge and actual progress need distinct evidence. The register asks whether the graph is adequate and proposes a later change if needed; it does not approve a specific new node. **[ENGINEERING PROPOSAL]** Use an explicit execution guard/evidence link rather than treating “aha” as progress. |
| Graph-to-policy documents | Register L12, F02-002; PRD L53/L67. | **[SOURCE] Requirement raised; [ENGINEERING PROPOSAL] implementation not approved as a final design.** Map conditions, actions, evidence and termination before proposing identity/soul/AGENTS documents. These filenames are conventions, not an inherited HAL API. |
| 60/40 independent base | Original L165 contains exploratory earlier ratios; L169 proposes 60% Capability and 40% Communication. Atlas H10 still displays approximately 50% Capability / 15–25% Mentality. PRD L58–59 makes current Plan 1 Technical 60 + Communication 40. | **[SOURCE] Current working Plan 1.** Use separate technical and communication arithmetic/evidence. Preserve H10 historically; do not use it in the current working scorer. Neither version is an empirically validated UK employer rubric. |
| Edge foresight within Technical | Original L157/L161; Atlas H05 is a separate evidence branch; PRD L59. | **[SOURCE]** Foresight is a Technical subdimension, not a third base category. The suggested approximately 20% of Technical is a candidate design, not an approved norm or an extra 20 overall points. |
| Optional bonus | Original L169 mentions 10–15%; PRD L61 reports latest preference up to +10 on the 100-point base. F06-002 is unavailable. | **[SOURCE] PRD attestation, not independently recovered conversational approval.** Keep the current working optional cap at +10, with a separate field and behavior evidence. Do not hardcode a positive award, subtract personality points, or claim direct review confirmation beyond available evidence. |
| Communication as an entire process | Original L13/L21/L31/L37/L39/L53/L153/L165/L169; Atlas H06 is only one evaluation node; PRD L17–18/L49/L59. | **[SOURCE] P0 correction:** observe communication through every phase. A post-hoc H06 score or code test pass alone does not satisfy FR05. The phase observation matrix below is a proposed operationalization. |
| Multiple meanings of “observed” | PRD L49 says `not_observed ≠ failed`; L59 lists `true/false/not_applicable/insufficient_evidence` separately from quality, confidence and event IDs; proposed schema L73 calls it `binary_presence`. | **[ENGINEERING PROPOSAL]** Preserve the four-state meaning; a Boolean-only field would lose information. Track opportunity, state and quality separately. A missing event cannot be silently scored as a failed behavior. |
| Platform timing | Atlas A12/J13/J14 are FUTURE; K12 says business process redesign precedes engineering. PRD L77–88 now requests architecture/mapping and bounded isolated prototyping immediately. | **[SOURCE]** The new execution instruction permits parallel safe prototype work; it does not freeze draft behavior, authorize live API cost/publication or turn the old Atlas future label into a permanent prohibition. |
| Test percentage / repair semantics | Original L59–111/L127–143; Atlas F04/F07; PRD L40. | **[SOURCE]** 4/20 and 80/20 are examples, not thresholds, percent code complete or automatic partial-credit amounts. A single ordering error may affect many tests; structural omissions need their own diagnosis. |
| Duplicate scorecard SVG edges | Atlas 06 has 43 rendered edge elements. Across all diagrams: 226 rendered edge elements but 202 distinct diagram/title/label triples. | **[SOURCE] Rendering duplication observed:** 24 excess repeated edge renderings, all in 06. Do not treat rendering multiplicity as repeated evidence or scoring weight. The CSV preserves actual edge references, rather than silently fabricating unique logical policy edges. |

[RESEARCH PENDING] Employer prevalence of interview formats, interviewer help frequency/thresholds, company scoring rules, timing expectations, sentiment/personality assumptions, and transfer effectiveness are unverified. An interviewer-led bounded session and SQL/data-transformation first case are working choices in PRD L15, not prevalence claims. Sponsorship is contextual source material, not a technical or communication score.

## 3. Traceability artifact and interpretation

[SOURCE] [SOURCE_TO_GRAPH_TO_REQUIREMENT.csv](SOURCE_TO_GRAPH_TO_REQUIREMENT.csv) contains **36 mapping rows**: 22 contract/behavior rows plus **14 phase-specific Communication rows**, covering **FR01–FR10**. Each row records canonical original line spans, actual node IDs/labels and original node status, actual SVG edge titles, diagram-qualified DOM IDs, raw labels and HTML line numbers, PRD line spans, verified issue references where applicable, and limitations.

[ENGINEERING PROPOSAL] An acceptance-evidence cell is a proposed way to demonstrate a contract; it is not a report that a test already passed. A `SOURCE` row is grounded in original/PRD wording but may still be a working hypothesis. A `USER-APPROVED` row here specifically refers to F01-001 evidence. Communication matrix rows are labeled `ENGINEERING PROPOSAL` because their concrete observation treatment is newly specified, although P0 Communication itself is a direct PRD requirement.

[SOURCE] `UNVERIFIED` in the issue column means no applicable issue linkage was established from available review records; it does not imply that a requirement was rejected or that an unknown issue has been mapped. The missing four IDs are named only as unavailable records, never assigned invented content. Edge IDs such as `edge5` are scoped by diagram; use `01/edge5`, not an unqualified global ID. The CSV retains duplicates to identify the supplied rendering exactly; runtime semantic edge normalization requires an explicit proposed policy key/version.

## 4. P0 Communication observation matrix

[ENGINEERING PROPOSAL] The rows below define observations rather than extra score categories or a per-phase point allocation. They connect to the `CMxx` CSV rows, which carry exact source, graph and issue references. Interview phases, post-session review and training are distinct scopes; post-session speech must not silently improve a previously committed interview score.

| ID / phase | Observable communication | Required evidence / separate Technical boundary |
|---|---|---|
| CM01 · brief / rules | Candidate confirms task format and permitted resources; asks about unclear constraints | A time-stamped acknowledgment or focused question; if no response opportunity, insufficient_evidence. Technical correctness is not inferred from rule acknowledgment. |
| CM02 · restate / clarify | Restate inputs, outputs and constraints; ask a precise clarification; update understanding | Restatement, actual clarification question, interviewer reply and revised understanding. The B05 correction comes from F01-001; do not award communication credit merely for asking any question. |
| CM03 · initial plan | Explain a concise overall route or staged hypothesis and next verifiable objective | Plan statement tied to goal, assumptions and anticipated next test. Judge clarity separately from algorithm validity; familiar tasks need not receive long narration. |
| CM04 · trade-offs / challenge | Explain rationale, alternatives and constraints when challenged about a novel or slower route | Candidate rationale references task needs and acknowledges a relevant limitation. Different from canonical solution is not itself poor communication or technical failure. |
| CM05 · feedback interpretation | Restate specific feedback, describe needed behavioral change and connect to next independent action | Feedback event, candidate paraphrase and linked proposed/action/result events are separate records. Aha is insufficient for execution; clear paraphrase can coexist with technically unsuccessful action. |
| CM06 · implementation updates | State block purpose, explain meaningful operation/parameter choices, report intermediate status | Progress statement links a code version and what has actually been checked. Do not reward line-by-line verbosity or treat all typed code as an explanation. |
| CM07 · diagnosis / replan | Describe what is done, proven, unresolved, first divergence and a proposed next hypothesis | Structured failure narrative with validated-work references and a proposed smallest test. Distinguish technical diagnosis accuracy from communicative precision and honest uncertainty. |
| CM08 · permitted help request | Name precise gap, intended resource scope and proposed use; request permission before access | Request, policy decision, declared source and subsequent action are individually linked. No request is not failure on an independently solved path; persuasiveness cannot change permissions. |
| CM09 · refusal / independent fallback | Acknowledge refusal and communicate a feasible independent route or honest remaining limitation | Refusal acknowledgment and candidate next-decision record. Respectful rule compliance is observable behavior; do not infer submissiveness or personality. |
| CM10 · repeat blockage | Explain why the prior hint or attempt did not resolve the gap and update next decision | Second-round explanation cites prior attempt and distinguishes newly missing knowledge from repetition. Second blockage is an observation, not automatic loss of communication credit. |
| CM11 · test failure / partial progress | Contrast passing/failing cases, state limitation and next test without overstating completion | Failure narrative cites actual test evidence and acknowledges uncertainty about root cause. 4/20 is illustrative only; technical test success cannot substitute for communication observation. |
| CM12 · wrap-up / expiry | Concise recap of delivered result, trade-offs, remaining work and assistance used | Final statement tied to submitted version and verified completion boundary. If platform terminates without closing opportunity, mark insufficient_evidence; do not penalize accent or gratitude style. |
| CM13 · score review | Ask evidence-based questions about evaluation and identify disputed or missing observations | Review annotations cite score/evidence IDs and record corrections without rewriting history. Training communication observation by default; do not retroactively improve closed interview score. |
| CM14 · training / repeat | Explain chosen practice gap, success criterion and later comparison with prior conditions | Drill plan and later reflection link real session IDs and measured evidence. Practice/review are separately scoped observations; no invented improvement before second execution. |

### Proposed observation record and scoring discipline

[ENGINEERING PROPOSAL] Record `session_id`, `phase`, `criterion`, `opportunity_event_refs`, `event_refs`, `observed`, `quality`, `confidence`, `independent_or_assisted`, `assessor`, `rubric_version`, and a concise evidence-based explanation. The first set of event references explains why a behavior could fairly be examined; the second identifies what the candidate actually did. New fields supplement the minimal PRD contract and need versioned review.

| Field/state | Meaning | Scoring treatment |
|---|---|---|
| `observed=true` | A target behavior or assessable attempt is recorded with event IDs. | Quality may be strong, limited or ineffective according to published anchors; presence alone earns no automatic full credit. |
| `observed=false` | A genuine opportunity was recorded but the target behavior was not observed. | Preserve as non-observation with reason; do not equate automatically with a failed behavior or zero quality. |
| `not_applicable` | Branch/behavior was not needed, e.g. no help request during independent success. | Do not penalize or require unnecessary assistance to fill the scorecard. |
| `insufficient_evidence` | No reliable opportunity, missing capture, premature interruption or ambiguous evidence. | Quality remains null/unscorable; expose evidence coverage and uncertainty. |
| Quality and confidence | Quality describes demonstrated behavior; confidence describes certainty of that judgment. | Separate values; no confidence-scaled arithmetic unless explicitly proposed and reviewed. |
| `independent_or_assisted` | Provenance of the work, including permitted aid and hint events. | Compare like conditions and preserve independent/assisted results; no inherited automatic hint deduction. |

[ENGINEERING PROPOSAL] Candidate quality anchors should evaluate precision, relevance, honesty and the connection between message and next action. A concise correct statement of a gap can be strong communication even when the candidate cannot implement the repair. An empty acknowledgment can be insufficient evidence of feedback-to-action even if a later test happens to pass. A clearly described but technically incorrect hypothesis must preserve both facts: communication can be assessable while technical correctness is low. Do not infer communication quality from total words, accent, speech speed, extroversion, perceived confidence, politeness style or sentiment.

[SOURCE] The current working display is `technical_base /60`, `communication_base /40`, `base_total /100`, optional `bonus /10`, and `illustrative_total` with provenance (PRD L59–61). [ENGINEERING PROPOSAL] If a domain lacks enough evidence, display an unscorable/incomplete subtotal and coverage rather than silently rescaling observed items to a full 60 or 40. A new weighting or missing-data normalization rule would be a change proposal. A demonstrated recovery episode may support a communication criterion and a bounded bonus only with distinct stated criteria; do not count the same vague “good attitude” twice.

### Proposed P0 verification cases

[ENGINEERING PROPOSAL] These are source-grounded verification requirements, not completed test results:

1. B05 YES clarifies and rechecks; NO proceeds. Source graph labels remain visibly different from approved semantics.
2. Two candidates give identical “I understand” responses; only the one with subsequent attempted/verified action receives progress evidence. Comprehension remains separate.
3. Successful code with no captured explanation does not fabricate communication quality; strong explanation with failed code does not inflate technical correctness.
4. Independent success has no required help-request evidence; refused help is followed by a logged independent decision or honest stop.
5. Second blockage records the new gap and previous attempt; neither repeated help nor apparent persuasion overrides policy.
6. Syntax/local output defect and structural omission take distinct diagnosis paths; 4/20 does not become a fixed scoring threshold.
7. Missing capture, unreached phase and negative observed behavior produce different observation states.
8. Separate technical/communication arithmetic is reproducible; foresight stays under Technical; bonus remains separate, bounded and evidence-backed.
9. Closed interview evidence is handed to Trainer; a later drill or review does not rewrite the closed score. No second session means no measured improvement delta.
10. Trace links resolve existing nodes, physical edge references and verified issue records; duplicate SVG arrows cannot multiply events or points.

## 5. Remaining decisions and safe engineering boundary

[SOURCE] Work can continue on isolated architecture analysis and bounded prototype acceptance fixtures under Rapid PRD L77–88. The missing review history does not require inventing approvals or waiting to perform already-authorized engineering discovery. Existing canonical source files were not edited by this audit.

[RESEARCH PENDING / DECISION REQUIRED] Obtain the actual conversational review or versioned entries F03-001/F04-001/F05-001/F06-002 to validate the unresolved review history. Confirm the intended detailed Communication anchors/weights, missing-evidence treatment, comparable-session conditions and policy mapping. Existing F01-001 approval stands; F01-002/F02-001 remain coverage corrections; F02-002 remains a proposal. Do not elevate these unresolved details to production policy by convenience.

[SOURCE] Publishing, external public commits/releases, credentials/paid API, deployment and material scope changes remain the explicit human-gate cases in PRD L85. The audit itself creates only this file and the CSV in the isolated output root; it does not mutate the repository snapshot, configure agents, disclose answer keys or claim production readiness.

## 6. Local source checks and fingerprints

[SOURCE] Completed checks: all original logical lines match Atlas source_lines; extracted Atlas DATA matches the full HTML embedded DATA; all mapped node IDs exist; all mapped edge titles resolve actual rendered elements; FR01–FR10 are covered; 14 Communication phase rows are present; all positively linked issue IDs exist in the register. These are source-integrity/trace checks, not MVP behavior test results.

| File | SHA-256 |
|---|---|
| `repo/integrations/virtual_technical_interviewer/粘贴的 Markdown (1)(6).md` | `a13bae60fddb97ccc76fd8bba55a3bc8481f4947b832a8ad256d4233814aa298` |
| `repo/integrations/virtual_technical_interviewer/index.html` | `e489b28d4298f4970e382cc4a7b35b9f68a618a4e0db0f7d491e7ffd788dfcbf` |
| `repo/integrations/virtual_technical_interviewer/Technical_Interview_MVP_PRD_RAPID_v0.1.md` | `dbfe27300629b30caef4879b55ae2527fd8663f1691fec7978e24d872ac3f686` |
| `repo/issue_register_v0_1.md` | `783b56fae5fa311dfdd257e7d4140d346618c50a9fa8c65c9960a245b3254779` |
| `repo/integrations/virtual_technical_interviewer/00–08 逐图评审对话.pdf` | `c934ed08236bc48fe7f77cc377595852d1536dff4bee637a19a2210b08ea63c6` |
