# Reference → Template: the generative function

## Why this skill exists
The moat is not the PRD's current domain nouns or impressive layout. It is an operator who can receive an entangled, nontechnical demand and recover the decision architecture necessary to build and evaluate the right product. A reference sentence is evidence of a previously chosen solution path—not a rule that every future product should implement that path.

## Nine-step transformation for EVERY meaningful unit
1. **Locate**: record `source_id` + exact page/slide/paragraph/cell or table shape. Do not reflow a slide as a plain prose paragraph without keeping its visual grouping.
2. **Atomic proposition**: break mixed statements into *fact / claim / desired outcome / proposed mechanism / numerical estimate / permission / decision / open question*.
3. **Ask why it exists**: identify its target reader and decision: why now, why this feature, why this boundary, how approved, what cost, what test.
4. **Strip particulars**: replace unique firm/department/model/vendor/date/amounts with typed slots—not just generic nouns but what makes them legitimate.
5. **Find invariant**: identify portable principle, e.g. “user-specific resource access cannot be inferred from job title” rather than “market cannot read trading files”.
6. **State conditional trigger**: `IF [Need/domain/context presents condition X] THEN [discover facts Y; evaluate trade-off Z; generate artifact W] ELSE [mark N/A with reason]`.
7. **Derive acquisition questions**: what must be known to responsibly generate this paragraph from a new Need? Make questions conditional on decision impact and be explicit about blockers.
8. **Author the meta paragraph**: imperative writing instruction with variables, evidence requirements, output schema, errors, acceptance, owner. It must work with unknown future needs.
9. **Test reverse generativity**: invent a non-financial, unrelated domain; verify the generalized rule produces a structurally appropriate paragraph without importing case-specific assumptions.

## Formal transformation record
```yaml
source_unit: Sxx/page-or-slide/paragraph
source_statement_type: fact | opinion | hypothesis | policy | option | scope | quantity | interface | acceptance | visual_relation
intent: which decision this source passage served
actor: who acts or owns the decision
invariant: principle that survives domain change
trigger: when the section is required
questions: facts to elicit from a new demand
slots: typed variables, no borrowed proper nouns
meta_instructions: rules for generating the new paragraph
output_contract: section/table/diagram
verification: observable check / falsifier
exclusions: copied numbers/vendors/credentials/uncorroborated claims
confidence: high | medium | requires_human_review
```

## Five high-value transformations

### A. A source says “our organization must build a central security database and send authorized data to individuals”
**Meaning**: system has heterogeneous information sensitivity and different readers.
**Invariant**: resource and action permissions must be explicit and testable across security boundaries.
**Writer rule**: IF the Need includes multiple identities or regulated/confidential information, enumerate data classes, actors, actions, access checks, exceptions, retention, audit, denied cross-boundary paths and tests. ELSE document the simple single-user boundary and explain absence of RBAC.
**Meta paragraph**: “For [information classes], adopt [policy model] at [granularity]. Permit [role] to perform [action] on [resource] only when [authorization predicate] is true; log [audit event], deny [negative scenario], and test with [fixture]. The owner of this policy is [data steward].”

### B. A source budgets 3 people × 3 months, tokens, external data and expected five-equivalent workers
**Meaning**: decision maker wants full economic liability and opportunity value visible.
**Invariant**: never quote one total without cost drivers, units and measurable benefit comparators.
**Writer rule**: elicit work packages, person-days, actual rates, usage distribution, provider billing, license status, hosting/security/support, buffer; choose low/base/high; show value baseline and attribution. Do not treat any figure from the old case as a default.
**Meta paragraph**: “Initial build cost = Σ(person-days_i × verified rate_i) + integration fixed charges + test/security + contingency. Recurring operating cost = model usage + infrastructure + third-party fees + maintenance. Expected benefits are [baseline] improved to [target] for [population] by [date], measured by [method], with uncertainty [range].”

### C. A source creates a red/blue investment committee with named third-party tools
**Meaning**: the task is judgment-heavy, uses specialist evidence and needs adversarial review.
**Invariant**: structured evidence/review gates matter, not five roles or any one provider.
**Writer rule**: IF decisions are high-stakes or contestable, require proposal → evidence → independent challenge → reconciliation → human decision, with claim provenance. ELSE use lighter single-step review and justify omission.
**Meta paragraph**: “For [decision], define the evidence collector, hypothesis proposer, independent challenger and accountable approver. Each returns [contract]; disagreements trigger [resolution rule]; no final result is accepted until [quality gate] passes.”

### D. A source shows a PPT Gantt running parallel tracks across several months
**Meaning**: dependencies, responsibilities and sequencing are materially important.
**Invariant**: visualize deliverables and critical path, not merely calendar dates.
**Writer rule**: build week × workstream matrix with action→artifact→owner→dependency→exit test; critical-path prerequisites determine earliest start. Place unknown vendor lead times as ranges.
**Meta paragraph**: “Workstream [X] can begin after [dependency]. During [window], [owner] produces [artifact], tests [condition], and escalates [risk]. Passing this gate unlocks [next work].”

### E. A source mockup specifies Chinese UI, dropdown modes, voice, memory and multi-agent flow
**Meaning**: a domain workflow must be made cognitively accessible to specific users.
**Invariant**: user journey is specified through states, tasks and visible outcomes, not decorative controls.
**Writer rule**: for each Persona/Job specify first-run steps, one gold path, loading, permissions, failure/retry, memory controls, ability to verify claim/source and export. List modes only when justified by distinct jobs.
**Meta paragraph**: “When [user] attempts [job] from [entry state], show [controls], perform [domain-specific mechanism], return [observable deliverable] within [performance target], and provide [failure/override/review] for [edge case].”

## Anti-overfitting tests
- Hospital appointment scheduling: can the rules produce role grants, operational flow, supplier interfaces, cost/value and acceptance without inventing a fund manager?
- Warehouse returns processing: can the model turn scattered process notes into a no-AI viable deterministic workflow and optional AI augmentation?
- Educational content authoring: can the rules permit a role-light, lower-security system without blindly importing enterprise-style three-tier restrictions?

## Typical mistakes
- Rename businesses but preserve old decisions and vendor stack.
- Copy targets, salary figures or model fees from old sources.
- Equate “has a mockup” with “has an integrated backend”.
- Skip null cases or invent data instead of labeling `TO_VALIDATE`.
- Treat project team's personal opinions as regulatory policy.
- Dump all raw source into PRD without constructing an evidence chain.
