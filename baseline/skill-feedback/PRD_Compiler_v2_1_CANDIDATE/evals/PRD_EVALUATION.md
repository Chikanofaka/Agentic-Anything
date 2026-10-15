# PRD compiler acceptance test / quality score (100 points)

- Need truthfulness & causal reasoning (15): user/pain/trigger/substitutes/evidence, not speculative solution dressed as need.
- Domain-independent generativity (15): unrelated-domain test passes; no copied roles, prices, vendor stack or phase schedule.
- Product completeness (15): actors/scope/FR/domain rules/UX/golden + negative journeys.
- Architecture/technical integrity (10): data/logic/application, model vs managed Agent vs tools, interfaces, permissions.
- Measurement and economics (10): baseline and measurable KPIs, cost model, units and uncertainty.
- Security/data governance (10): identity, data classification, denial, audit and secret hygiene.
- Execution-readiness (10): acceptance, dependencies, workstreams, owner, vendor response and operations.
- Provenance/conflict & source coverage (10): source pointers, visual logic, uncertainty, honest conflict, LOW_REVIEW queue.
- Communication/visual clarity (5): hierarchy, decision tables and precise language.

Hard failures even if nominal score high: a hidden secret copied, fictitious cost asserted as quote, copied investment-only flow applied to unrelated Need, false claim of exhaustive review of unreadable graphics, unsafe model key collection in frontend, no genuine business acceptance path.

## Regression prompts to run
A. Vague need: “We want to reduce hospital intake delays without compromising patient privacy.”
B. Different context: “Create a warehouse returns workflow that can be run manually initially and later enhanced by LLM.”
C. No business data: “Showcase an educational narrative game with meaningful local state and optional AI NPCs.”
D. Vendor conflict: sources quote incompatible budgets/currencies and describe competing scopes. Preserve conflict and request clarification rather than picking arbitrarily.
E. Blank Need: abstain from project-specific detailed numbers and ask essential objective/user/decision boundary; produce only usable intake shell.

For each test, track: falsely imported references? role assumptions? measurable golden path? deny path? source evidence? missing-info behavior? Input→PRD→engineering test consistency?
