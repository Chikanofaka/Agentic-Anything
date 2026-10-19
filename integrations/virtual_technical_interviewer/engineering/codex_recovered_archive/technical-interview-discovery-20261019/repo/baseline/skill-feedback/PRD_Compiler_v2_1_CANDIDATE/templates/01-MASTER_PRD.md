# MASTER PRD TEMPLATE — Fill only from a NEW Need (not old project content)

> Every item below is a generative contract. Insert verified new-case facts in `{}` slots; keep `[UNKNOWN]` or `[ASSUMPTION]` with decision owner if unavailable. Do not copy the original case-specific details.

## Compiler rules
For each chapter: (1) declare target reader/decision; (2) derive content from normalized Need & source evidence; (3) request material missing values; (4) write assertions with provenance status; (5) define test/false case; (6) cross-reference earlier chapters.

## 00. Document control, audience & decision
**Why this section exists:** enables stakeholders to decide decision sought; version; owner; approval authority; governing source baseline.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Decision sought; version; owner; approval authority; governing source baseline. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Document contract, change log and source statuses.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 01. Executive decision summary
**Why this section exists:** enables stakeholders to decide why now, existing cost, minimum value, differentiated proposal, tradeoffs.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Why now, existing cost, minimum value, differentiated proposal, tradeoffs. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** One-page WHY/WHAT/HOW/VALUE/COST/ACCEPTANCE.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 02. Problem evidence and Need trace
**Why this section exists:** enables stakeholders to decide actor, pain, current workflow, frequency, severity, source quality, current substitute.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Actor, pain, current workflow, frequency, severity, source quality, current substitute. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Evidence table and observable pain statement.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 03. Business strategy and product definition
**Why this section exists:** enables stakeholders to decide capability ownership, strategic direction, differentiation, explicit anti-goals.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Capability ownership, strategic direction, differentiation, explicit anti-goals. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Positioning sentence and strategic alignment map.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 04. Goals, metrics and falsifiers
**Why this section exists:** enables stakeholders to decide baseline, cohort, observable benefits, risk ceilings, conditions that kill idea.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Baseline, cohort, observable benefits, risk ceilings, conditions that kill idea. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** North-star, leading/lagging KPI contract.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 05. Target users, stakeholders and responsibilities
**Why this section exists:** enables stakeholders to decide actor categories, differing jtbd, decision rights, raci.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Actor categories, differing JTBD, decision rights, RACI. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Persona matrix and business responsibility map.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 06. As-is journeys and bottlenecks
**Why this section exists:** enables stakeholders to decide journey steps, handoffs, data movement, timing, errors, workarounds.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Journey steps, handoffs, data movement, timing, errors, workarounds. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Current-state service blueprint.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 07. Future-state service blueprint
**Why this section exists:** enables stakeholders to decide expected user actions and system responsibilities, transitions and special paths.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Expected user actions and system responsibilities, transitions and special paths. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** To-be user/system swimlane.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 08. Scope, release stages and exclusions
**Why this section exists:** enables stakeholders to decide mvp shortest complete value loop, deferred modules, hard exclusions, criteria for expansion.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** MVP shortest complete value loop, deferred modules, hard exclusions, criteria for expansion. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** NOW/NEXT/LATER/NOT-PLANNED table.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 09. Capabilities & functional requirements
**Why this section exists:** enables stakeholders to decide each function fr-id; user trigger, i/o, business rules, ui state, error, acceptance.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Each function FR-ID; user trigger, I/O, business rules, UI state, error, acceptance. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** FR matrix and scenario contracts.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 10. Information architecture and user experience
**Why this section exists:** enables stakeholders to decide navigation, devices, onboarding, accessibility, loading/error/success, exports, state persistence.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Navigation, devices, onboarding, accessibility, loading/error/success, exports, state persistence. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** UX state map, screens, accessibility and copy principles.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 11. Account, identity and permission design
**Why this section exists:** enables stakeholders to decide identity model, authorization granularity, roles, exception grants, scoped actions.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Identity model, authorization granularity, roles, exception grants, scoped actions. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Role × asset × action × condition matrix.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 12. Data inventory and information lifecycle
**Why this section exists:** enables stakeholders to decide sources, rights, formats, owners, schemas, frequency, lineage, retention.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Sources, rights, formats, owners, schemas, frequency, lineage, retention. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Data catalog, refresh policy, quality gates.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 13. Data governance and trust boundaries
**Why this section exists:** enables stakeholders to decide data classes, external exposure, dlp, audit, export, deletion, threats.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Data classes, external exposure, DLP, audit, export, deletion, threats. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Threat model, authorization examples, negative tests.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 14. Three-layer architecture
**Why this section exists:** enables stakeholders to decide input/data, logic/security/inference, application/presentation and arrows.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Input/data, logic/security/inference, application/presentation and arrows. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Layer ownership and system boundary map.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 15. Domain knowledge & specialist methods
**Why this section exists:** enables stakeholders to decide required fixed method, allowable generation, templates, evidence grading.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Required fixed method, allowable generation, templates, evidence grading. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Domain contract and hard/soft constraints.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 16. Business workflow / agent orchestration
**Why this section exists:** enables stakeholders to decide route, workers, tools, artifacts, mandatory gates, state transitions.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Route, workers, tools, artifacts, mandatory gates, state transitions. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Workflow table/diagram and recovery state machine.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 17. Vendor, model, API and tool dependencies
**Why this section exists:** enables stakeholders to decide adapter family, auth, licensing, latency, input/output schema, quota, procurement.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Adapter family, auth, licensing, latency, input/output schema, quota, procurement. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Provider capability matrix and fallback.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 18. Memory, context, edits and citation
**Why this section exists:** enables stakeholders to decide what persists, corrections, version trace, citation granularity, deletion rights.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** What persists, corrections, version trace, citation granularity, deletion rights. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Memory/state model and version-change scenarios.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 19. Non-functional requirements
**Why this section exists:** enables stakeholders to decide performance, availability, security, accessibility, retention, scalability, portability.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Performance, availability, security, accessibility, retention, scalability, portability. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** NFR with measurement and error budget.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 20. Key scenarios and mockup specification
**Why this section exists:** enables stakeholders to decide first run, normal job, escalation, error, absent integration, review & export.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** First run, normal job, escalation, error, absent integration, review & export. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Screens/specs and realistic golden task script.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 21. Economics: cost structure
**Why this section exists:** enables stakeholders to decide work package person-days, inference, infra, license, staffing, testing, support.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Work package person-days, inference, infra, license, staffing, testing, support. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Cost drivers with currencies, units, scenarios.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 22. Business value and ROI
**Why this section exists:** enables stakeholders to decide labor, cycle-time, throughput, decision quality, risk reduction, measurable benchmarks.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Labor, cycle-time, throughput, decision quality, risk reduction, measurable benchmarks. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Side-by-side cost/value and unit economics.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 23. Supplier scope / request for proposal
**Why this section exists:** enables stakeholders to decide deliverables, ownership, solution assumptions, procurement status, vendor slas.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Deliverables, ownership, solution assumptions, procurement status, vendor SLAs. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** RFP/RFQ package and mandatory response.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 24. Risks, assumptions, alternatives
**Why this section exists:** enables stakeholders to decide top risks/failure mechanisms, testable assumptions, no-build, recovery and stop conditions.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Top risks/failure mechanisms, testable assumptions, no-build, recovery and stop conditions. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Risk register with owners/falsifiers.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 25. Quality gates and acceptance testing
**Why this section exists:** enables stakeholders to decide given/when/then, source validation, negative tests, security tests, signer.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Given/When/Then, source validation, negative tests, security tests, signer. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Acceptance matrix with evidence links.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 26. Milestones, dependencies and resource plan
**Why this section exists:** enables stakeholders to decide workstreams, week-by-week deliverables, staffing, critical path, buffers.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Workstreams, week-by-week deliverables, staffing, critical path, buffers. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Multi-workstream matrix and WBS/Gantt.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 27. Operations and change management
**Why this section exists:** enables stakeholders to decide deployment, observability, incident, training, support, rollback, migration.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Deployment, observability, incident, training, support, rollback, migration. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Release runbook, operations acceptance.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 28. Decision governance and signoff
**Why this section exists:** enables stakeholders to decide pending choices, proposed options, rationale, approvers, revision policy.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Pending choices, proposed options, rationale, approvers, revision policy. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Decision log, human gate, vendor receipt and signoff.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 29. Appendix: traceability and source map
**Why this section exists:** enables stakeholders to decide link each fr and claim to need, source unit, test and artifact.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Link each FR and claim to Need, source unit, test and artifact. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** N→FR→AC trace and visual conversion index.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 30. Professional slide / diagram blueprint
**Why this section exists:** enables stakeholders to decide story order, diagram type, table schema, visual hierarchy and reading flow.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Story order, diagram type, table schema, visual hierarchy and reading flow. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Decision-level PPT/visual appendix.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?

## 31. Engineering handoff and next learning experiment
**Why this section exists:** enables stakeholders to decide open issues, contract interfaces, minimum validation, non-goals, work breakdown.
**New-Need extraction questions:** What is the {actor}, {trigger}, {baseline}, {desired state}, {constraint}, {data / role / external dependency}, {uncertainty} and {decision owner} relevant to this section? Omit irrelevant fields with rationale.
**What to write:** Open issues, contract interfaces, minimum validation, non-goals, work breakdown. Do not supply values from a historical example; derive from new intake evidence, explicitly approved assumptions and newly verified technical constraints.
**Required artifact:** Builder-ready handoff with no ambiguity left hidden.
**Paragraph generator:** “For `{actor}` doing `{task}` under `{constraint}`, the product shall `{outcome}` by `{mechanism or business rule}`. Its input is `{input}`, output is `{output}`, permission and failure handling are `{control}`, baseline and target are `{KPI and observation period}`, evidence is `{provenance}`. If a field is absent, mark it `TO_VALIDATE` and name the blocker.”
**Check:** Is the text sufficiently specific for two independent builders to produce the same observable behavior? Which counterexample would make the requirement false?
