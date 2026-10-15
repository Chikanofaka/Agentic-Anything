---
name: need-to-prd-reference-abstraction
description: Convert unstructured needs and historical PRD/proposal/slide/workflow references into a domain-agnostic, decision-grade, engineer-ready PRD by deriving the generating principle behind each source unit. Uses paragraph-level provenance, visual-logic conversion, quantitative assumption controls, three-layer architecture, scenario contracts and human acceptance gates.
---

# Need → PRD | Reference-to-Template Compiler v2.1 CANDIDATE (HAL pilot)

## Mission
The input is a Need (possibly contradictory, entangled, incomplete, and nontechnical) plus zero or more source PRDs, proposals, slide decks, diagrams and operational matrices. Output a NEW PRD for that Need, matching the depth and completeness of decision-grade references without copying their domain-specific people, products, numbers, vendor choices, assumptions, features or designs.

**Do not start by writing the new project's content. Start by learning the generating function.**

## Mandatory loading sequence
1. Read `references/01-CONVERSION_KERNEL.md` — original claim → intent → invariant → conditions → generative instruction → meta paragraph → falsification.
2. Read `references/02-SOURCE_ATLAS.md` and `references/03-VISUAL_SOURCEMAP.md` — source structure and slide/diagram logic.
3. Read `references/04-GENERATIVE_OPERATORS.md` + `references/ABSTRACTION_RULE_LIBRARY.json` — domain-neutral rules.
4. Read `templates/00-NEED_INTAKE.md`, `templates/01-MASTER_PRD.md`, and specialized templates invoked by the case.
5. Read `references/05-QUALITY_AND_CONFLICTS.md`, `evals/PRD_EVALUATION.md`; never omit qualification/reality status.
6. Read `references/07-PILOT_RECURSION_RULES.md` and apply explicit stale-result, historical-progress, port-capability and section-specificity gates.
7. If a source-conversion audit is requested, consult `ledger/paragraph_to_template_ledger.csv` (located beside the skill package) with precise file/page/slide/cell source pointers; reinterpret LOW_REVIEW units rather than assuming machine assignment is correct.

## Core function
`PRD = G(Need, Evidence, Stakeholders, Constraints, Templates, Decisions)`.
For each source unit `u`: `extract(u) → proposition(u) → intentional rationale(u) → domain-invariant(u) → conditions(u) → open questions(u) → reusable rule(u) → meta-paragraph(u) → validation(u) → trace(u)`.

Never merely replace “基金经理” with “[用户]” or “Wind” with “[API]”. Reconstruct **why** the paragraph exists, which decisions it supports, what conditions make it necessary, how a PRD writer should discover missing facts, and what measurable evidence would make its claims true.

## Hard rules
- **Need is input; PRD is a proposed implementation and business design, not validated need evidence.** Separate observed facts, stakeholder assertions, hypotheses, proposed mechanisms, assumptions, estimates, vendor quotations, decisions and test outcomes.
- Decompose a tangled Need as actor × pain × workflow × value × constraints × dependency × risks; dedupe and separate means from ends.
- Every recommended feature must map Need→Job→Scenario→FR→Interface/Workflow→Data/Permission→Acceptance→Owner.
- Every numeric claim must specify units, period, population, baseline, source, estimator, uncertainty and verification. Historical figures are NEVER default costs or ROI for a new project.
- Every external integration must be classified: model API, managed-agent API, embedded agent channel, data feed, normal tool/API, people service, or infrastructure. Do not equate provider and API key with an entire runtime.
- Every sensitive datum must be permission-reviewed before appearing in a generated artifact. Do not reproduce passwords or live credentials found in references.
- Every illustrative mockup must say REAL / SIMULATED / ASSUMED / OUT_OF_SCOPE, and every acceptance criterion must include a negative test and evidence of completion.
- Ask only blocking questions; otherwise work from explicit assumptions marked TO_VALIDATE, prioritize by consequence and place unknowns in a decision register.
- Do not collapse changing versions of a plan into one false consensus; preserve conflicts and dates.
- Do not turn stakeholder objectives or estimates into verified performance or vendor commitments.
- Decide what belongs in PRD and what belongs in engineering solution assumptions. Architecture suggestions are falsifiable, not immutable commands to implement a named stack.

## Content completeness contract
Minimum sections: document contract; Need evidence; goals/JTBD; scope/non-goals; role and permissions; functional/interaction design; data & knowledge assets; logical and three-layer architecture; workflow/state machine; integrations; memory/audit; risk, economics/ROI; test/acceptance; delivery plan; vendor response; decision/assumption ledger; provenance; appendix.

Require at least 1 measurable golden scenario and 1 adverse scenario. For complex projects, add reusable feature matrix, account matrix, data inventory, provider capability matrix, cost↔value two-column model, workflow graph, Gantt/workstream matrix and RACI.

## Deliverable behavior
A. Produce `NEED_NORMALIZED.md` from the raw input, retaining verbatim facts only in a restricted evidence file when necessary.
B. Produce an original complete `PRD.md` using the master template and applicable modules; never copy a past project's actual solution as current truth.
C. Produce `ASSUMPTIONS_AND_OPEN_QUESTIONS.md`, `TRACEABILITY.csv`, `ARCHITECTURE_OPTIONS.md`, and `UAT_MATRIX.md`.
D. For source abstraction tasks: produce an exhaustive source-unit ledger with source/position/hash, generic conversion rule, intended output, confidence, and explicitly listed image-only review debt.
E. Return a `PRD_QUALITY_RECEIPT.md` with completeness, assumptions, contradictions, negative test coverage and Human Gate status.

## Human Gate
A draft is not automatically approved. Human may choose APPROVE_FOR_ENGINEERING / MODIFY / PARKED / BLOCKED. Engineering approval is not publication approval.

## Experimental v2.1 promotion gate
This is a candidate fork generated during HAL Pilot. Run `evals/HAL_PILOT_REGRESSION.md`, get human reviewer approval, and verify unrelated-domain behavior before replacing an installed authoritative skill. Never claim automatic installation or self-training.
