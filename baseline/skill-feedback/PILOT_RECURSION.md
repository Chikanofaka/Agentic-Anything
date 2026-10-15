# HAL Pilot v2 — Recursive Skill/Idea Improvement Receipt

## Closed-loop protocol (initialized, not falsely claimed autonomous)
`INPUT user Need → normalize Need → diverge solution candidates → select provisional idea → compile 32-section PRD → enforce FR trace and UAT → build direct-fidelity MVM → machine tests → discrepancy log → proposed Skill patch → Human UAT → Human decision → (authorized only) engineering → collect observed outcomes → re-run compiler`.

The current loop has completed **through automated Ready evaluation and proposed patch**. The human review and any real deployment data are **PENDING**. There is no autonomous background self-training, self-editing installed plugin, or fabricated external adoption signal.

## v1 → v2 baseline differences / observations
| Dimension | v1 PRD/MVM baseline | v2 pilot change | Confidence / residual gap |
|---|---|---|---|
| PRD coverage | ~14 topical sections, adequate high-level framing | 32/32 specific master sections with section-specific decisions, conditions and contracts | Explicit section scan; human still must assess usefulness |
| Direct product mechanism | dual pathway then one research calculator | same shell swaps Research/Returns; different source ZIP, README, bindings and real domain outcomes | Browser + CLI tested fixtures; still hardcoded examples, not arbitrary source plug-ins |
| Traceability | list of FRs and acceptance but no machine-readable full chain | N01–N06 → F01–F16 → T01–T16 → permissions/output | CSV verified; some requirements remain Doing-only |
| Model honesty | simulated inference declared | explicit typed model/managed agent/tool ports and incompatibility block | MVM simulation only, no actual model tested |
| UAT | five-minute journey and feedback export | cross-domain magic moment, 5 progress missions, two real domains, invalidation of stale result | 36/36 browser checks; UAT by human pending |
| Recursive learning | manual follow-up needed | automated discrepancy→patch candidate and regression protocol | Not autonomously self-improving; adoption feedback not collected |
| Economic reasoning | generic formulas, no quote | explicit work-package drivers, unit/period/price status, open decision ledger | cost quantities still unknown; do not invent |

## Actual discrepancies found by pilot (not hypothetical)
### P-01: Template anti-pattern — repetition without decision logic
The v2 `01-MASTER_PRD.md` repeats nearly the same generic paragraph generator and extraction question across 32 chapters. Without a supplemental instruction, an LLM can technically fill them with repetitive prose that does not resolve the section's own decision. **Proposed fix:** require each chapter to name its unique decision, input evidence, artifact type and falsifier; score chapter-level specificity, not just presence.

### P-02: Demo trust bug — stale result after invalid input
Initial HAL v2 MVM kept a successful previous calculation available after a new invalid input was entered. That risks exporting a result that appears to correspond to the latest task. **Fixed in this v2 deliverable:** invalid input clears current result/report and forces recalculation. **Skill patch:** include stale-result invalidation as a negative test for every stateful or report-export workflow.

### P-03: Demo mission progress initially lost after simulated disconnection
The first test did not show 5/5 after disconnect because the mission measured current activation state rather than the historical fact that preflight was attempted. **Fixed in this v2 deliverable:** separate `everPreflight` (learning completion event) from `preflight` (current connection state). **Skill patch:** distinguish historical milestones from current operational state explicitly.

### P-04: Strict generalized claim versus hardcoded domain fixtures
Two seeded client-side profiles show UI/logic reuse but are not evidence the runtime loads arbitrary domain repos. **Fix in wording:** label curated hardcoded fixtures and prohibit claims of deployed plugin architecture; specify Doing test using two audited real repos and unchanged HAL core.

### P-05: Provider compatibility must be typed, not name based
Demo accepts only two providers for simulation, but does not actually verify API capability; Manus is a separate managed-agent port. **Skill patch:** require a provider capability evidence column and verification before a feature can be labeled operational.

### P-06: Human Gate need not equal complete recursion
A template can look complete while key quantitative evidence and real user feedback are missing. **Skill patch:** separate `DOCUMENTATION_COMPLETE`, `READY_FOR_HUMAN_UAT`, `ENGINEERING_VALIDATED` and `MARKET_VALIDATED` metrics. Never collapse them into one '100%'.

## v2.1 candidate update (included, not installed)
Files under `skill-feedback/PRD_Compiler_v2_1_CANDIDATE/` extend the earlier reference skill with `references/07-PILOT_RECURSION_RULES.md` and `evals/HAL_PILOT_REGRESSION.md`, plus a start-of-run directive in a forked `SKILL.md`. Historical skill v2 remains untouched and verifiable.

## Proposed regression tasks for next PRD pilot
A. Warehouse returns Need: one domain workflow should be distinct from any imported investment-scoring system.
B. Generic UI but wrong backend: require genuine type/model port readiness and real domain actions; reject decorative chat.
C. Disconnect + input failure: ledger records historical milestones but final report is invalidated until a successful rerun.
D. Real provider swap: avoid treating a managed-agent task API as direct LLM model API.
E. Quoted budget conflict: require source/version, currency/units/quote and maintain OPEN decision rather than invented ROI.
F. No sources: abstain from fictitious user survey claims and label UX/MVM assumptions.

## Feedback decision needed
The Human Gate owner should judge (1) does the 2-domain behavior express a reusable generalizable mechanism? (2) is this stronger than a plain GitHub README+IDE? (3) should v2.1 PRD compiler patch be promoted, modified or parked? These decisions are not preselected.
