# Technical Interview Best-Practice Lab — Rapid MVP PRD v0.1
**Date:** 2026-10-18 · **Status:** Engineering discovery + bounded MVP prototyping authorized as a proposal; NOT a verified production design.  
**Audience:** Codex / Engineering Division · **Urgency:** Start independent technical planning now while strategic debate and full PRD proceed in parallel.

## 0. Binding source hierarchy — critical
1. **Primary intent:** `粘贴的 Markdown (1)(6).md` (entire source, not snippets).
2. **Primary process model:** previously reviewed `index.html` in `Interview_Process_Atlas_v0_1/` and its `00`–`08` charts; diagrams are **reviewed drafts, not frozen validated best practice**.
3. **Latest changes override earlier assumptions:** user-confirmed 00–08 conversational walkthrough and `issue_register_v0_1.md` (including F01-001, F03-001, F04-001, F05-001, F06-002).
4. **Explicitly excluded as product authorities:** any previous Technical Interviewer Agent PRD, including `Bad_Example_...` and v1/v2 handoffs. Do not use their requirements, architecture, weights, or acceptance criteria as inherited truth. General engineering practice may be proposed, clearly labelled as an engineering proposal.
5. Distinguish on every major clause: **[SOURCE] / [USER-APPROVED] / [ENGINEERING PROPOSAL] / [RESEARCH PENDING]**. Never silently turn Plan 1 hypothesis into a fact about UK employers.

## 1. Product objective and user outcome
**Build a repeatable real-world technical-interview decision-and-training loop — not a chatbot or a question-answer drill.** First model candidate *best-practice behavior* and interviewer *contingent reaction rules*; then create an adaptive **Interviewer Agent + separate Trainer Agent** so the candidate repeatedly practises strategy, technical execution, communication, agency, coachability, and recovery until behaviors transfer across unseen cases. UK/London experienced-hire technical interviews are a research context, **not** a universal assumption or hardcoded hiring rubric. Candidate personalization, company variation, visa/HR context can be added later.

**MVP target scenario [WORKING CHOICE, NOT PREVALENCE CLAIM]:** one bounded interactive, interviewer-led technical interview with calibrated possibility of silence, probing, refusal or permitted guidance. Include independent-solving branches. One complete interview → explainable scorecard → trainer-directed drill → repeat interview/compare. Prefer one technically executable SQL/data-transformation challenge as a proposed first case, subject to engineering validation; do not exclude future Python, modeling, debugging.

## 2. P0 system correction: Communication is a FIRST-CLASS process, not a footnote
Communication must be traced across **every interview phase** and have its own evidence and scorecard. On encountering limits, distinguish inability to solve the *structure* from forgetting a *syntax/function*; candidate should communicate **(a) what is done, (b) what is proven, (c) precise gap/risk, (d) independently proposed next step, (e) focused permitted help request, (f) action after the answer**. Evaluate actions/clarity, not charisma or perceived personality. Professional resource requests are allowed only under session policy; never pressure the interviewer to disclose answer keys or misrepresent competence. Observe whether the candidate translates feedback into autonomous progress; **mere agreement or “aha” does not prove execution**.

## 3. MVP end-to-end workflow and interacting state machines
**00 Strategy framing → 01 Dual-role workflow → 02 Interviewer reaction tree → 03 Candidate next-decision tree → 04 Coding/Debugging loop → 05 Final-pass / partial-failure recovery → 06 Evidence scorecard → 07 Trainer feedback/next practice → 08 Adversarial revision interface (manual, not auto-adoption).**

```text
PREPARE (question, allowed aids, time, disclosed rules)
   → GREET / BRIEF → QUESTION → RESTATE & CLARIFY
   → B05: requirements unclear? YES → clarify → re-check; NO → assess familiar/partial/unknown
   → articulate plan + trade-offs → staged implementation + explanatory communication
   ↔ interviewer's SILENCE / QUESTION / CHALLENGE / PERMITTED HINT / REFUSAL
   ↔ candidate interprets feedback → understands? → can ACT? → progress or stuck again?
      → syntax/local issue: local diagnosis, specific resource request if permitted, retry
      → structural issue: preserve validated work, revise plan / scope, retry
   → TEST/VALIDATE → all pass? YES → concise recap/optimization if time
                          NO  → compare passing/failing cases, preserve usable solution,
                                 isolate root cause, test smallest changed hypothesis
   → time/submit → evidence capture → technical + communication score + bounded bonus
   → explain score with traceable actions → trainer's targeted drill → next interview
```
**Correction already approved:** in 01/B05, **YES means clarify; NO means proceed to ability assessment**. Correct the diagram in a later controlled batch; do not treat the incorrectly labelled original edge as behavioral truth.

**Required reaction cases:** correct solution; near-correct with missed edge case; unusual valid but slower solution; fundamentally mistaken plan; syntax/function retrieval gap; complete blockage; feedback understood and executable; feedback verbally understood but no execution; repeat blockage; interviewer chooses silence, probing, limited nudge or denial; time expires; full test pass; partial pass with coherent subsolution. **80% / 20% progress and 4/20 tests are examples, not thresholds or pass rules.**

## 4. Functional contracts (MVP P0 unless marked)
| ID | Capability / behavior | Acceptance evidence |
|---|---|---|
| FR01 | User starts bounded interview; clear allowed-help policy; question and timer | Config + start/end logs; candidate knows rules |
| FR02 | Two-role sequential interaction and distinct interviewer choices | Replay shows interviewer action, candidate reaction, next decision at least two rounds |
| FR03 | Full blockage taxonomy, clarification, strategy replanning, syntax vs structural gap | Regression fixtures trigger different branches; B05 yes/no correct |
| FR04 | Candidate solution + test/diagnose/repair loop, preserve partial credit | Sample failed tests and revised attempt produce distinct, time-ordered records |
| FR05 | **Communication examination at EVERY phase** | Evidence entries for clarity, plan, progress updates, gap explanation, precise permitted request, response-to-feedback, wrap-up; `not_observed` ≠ `failed` |
| FR06 | Explainable technical/communication scorecard with evidence IDs | Each score tied to observable event and scoring method; independently solved vs hint-assisted separated |
| FR07 | Interviewer/Trainer separation and consistent policy | No unauthorized answer disclosure during interview; trainer sees committed evidence after close |
| FR08 | Targeted drill and next-session comparison | Trainer selects high-impact weakness; second session measurable delta, no invented improvement |
| FR09 | Editable rules mapped to graph nodes | Node/edge ID → conditions → permitted actions → logged events → assessment criteria |
| FR10 | Basic local text-first replayable UI (engineering proposal) | Start, converse, submit, review evidence/score and next drill in one environment |

**MVP non-goals:** automatic claims about dominant UK interview format; full employer-specific hiring algorithms; real visa decisions; full voice, live transcription, unrestricted AI browsing; paid API or deployment without approval; perfect question-bank breadth; pretending a static simulation used live model reasoning.

## 5. Scorecard: latest Plan 1, **not** an empirically validated employer rubric
**Base 100 points = Technical Capability 60 + Communication 40.** Within Technical, edge-case foresight is a **subdimension** (user suggested ~20% of *technical* as a candidate design, not approved norm), not a third independent category. Technical also measures planning, conceptual correctness, implementation, testing and repair. Communication independently measures task framing, concise stepwise reasoning, proactive progress updates, explicit failure narrative, precise collaborative request, respectful rule compliance, feedback-to-action and closing. Encode observability as `observed=true/false/not_applicable/insufficient_evidence` **plus separate quality rating, confidence and event ID**; absence alone does not prove poor quality.

**Optional bounded positive bonus** for observable resilience/professional composure/constructive connection: user latest preference **up to +10 points on a 100-point base**; not a deductive personality score and not a confirmed hiring standard. Show `technical_base`, `communication_base`, `base_total`, `bonus`, `illustrative_total`, and provenance separately. Resist hardcoding bonus if evidence insufficient. Preserve prior weight proposals only in historical research notes, not score computation.

## 6. Proposed technical boundary (subject to Codex repository audit)
- Inspect `Chikanofaka/Agentic-Anything` **current** HAL Type B domain interface and actual tests before proposing integration. Never presume dropping a plugin directory automatically registers a runnable domain.
- Conceptual layers: `question/test fixtures` → `interview policy/state/permissions` → `Interviewer response` ↔ `Candidate event stream` → `deterministic verification where possible` → `evidence ledger` → `scorer` → `Trainer drill` → `UI`.
- Source-of-truth: host-controlled time, allowed aid modes, score arithmetic, fixtures, logged events and answer secrecy; generative model creates language, not authoritative test outcomes or invisible event records.
- Create proposed `AGENTS.md` / `identity.md` / `soul.md` **only after mapping** rule clauses to approved diagram states; document policy precedence and note that these filenames are convention proposals, not the only valid HAL extension mechanism.
- Secure challenge execution: prefer deterministic sandboxed SQL fixtures; no executing untrusted arbitrary Python without isolation; handle data privacy and unknown provider/API cost explicitly.

## 7. Proposed data contracts (minimal)
- `InterviewSession`: id, question_id, mode, allowed_aids, started_at, expires_at, state, policy_version, rubric_version.
- `TurnEvent`: id, seq, actor, action, graph_node_id, graph_edge_id, timestamp, text_or_artifact_ref, hint_level, source_kind.
- `AssessmentEvidence`: id, event_refs, skill, binary_presence, quality, confidence, independent_or_assisted, assessor, explanation.
- `Scorecard`: technical_60, communication_40, optional_bonus_0_10, breakdown, source_version, unscorable flags.
- `TrainerPlan`: prioritized gap(s), drill objective, success measure, source_score_events, next_session_ref.

## 8. Codex execution now — parallel engineering request
**Do not wait for full PRD or further adversarial debate.** In an isolated workspace:
1. Inspect the existing repo/HAL, test suite and 00–08 atlas; produce `ARCHITECTURE_READINESS.md`: current integration entrypoints, versioned interfaces, unknowns, risks and least-invasive MVP approach.
2. Build `SOURCE_TO_GRAPH_TO_REQUIREMENT.csv` for all P0 behaviors, with exact source line numbers / graph node IDs / issue-register IDs. Clearly separate user intentions from unverified market assumptions and engineering inferences.
3. Propose `MVP_IMPLEMENTATION_PLAN.md` with modules, incremental testable work packages, estimate/risk, no silent provider assumptions. Implement an isolated local prototype only if safe/authorized by repo procedures; do not mutate existing public code or publish materials by default.
4. Prepare tests for B05 correction; feedback understood vs action; repeated stuck; local vs structural failure; full pass vs partial progress; policy-refused hints; privacy/answer-key leak; scored communication evidence; separate bonus; Trainer handoff.
5. Report actual `PASS/FAIL/NOT_RUN`, clickable local demo/commands if available, and `DECISIONS_REQUIRED.md`. Don't claim full MVP or market validation from generated docs.

**Human Gate:** ask approval only for external public commits/releases, credentials/paid API, deployment, or material scope changes. The owner will continue research and debate in parallel; every new decision becomes a versioned change proposal, not an automatic silent rewrite of the baseline.

## 9. Definition of ready / success for this rapid handoff
This document is **enough for Codex to analyze architecture, map requirements, estimate and begin safe, isolated prototyping**. It is **not** the promised full PRD, final market study, frozen hiring rubric, user-accepted engineering architecture, or evidence that a working product exists. The full PRD will expand into line-by-line fidelity, granular behavioral rules, communication examination table, feature contracts, adversarial UAT and deployment decision.
