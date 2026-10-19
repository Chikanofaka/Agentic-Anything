# HAL v2 — Assumptions, Questions and Decisions

## Evidence disciplines
USER_STATED: two-path requirement, local-first downloadable package idea, Key Academy and editable UI. BASELINE_DOCUMENT: v1 PRD/MVM deliverables. PROPOSAL: v2 selected product mechanism. VERIFIED_TEST: CLI fixture + browser UAT only after actually executed. ESTIMATE: engineering days/cost hypotheses need real owner inputs. OPEN: facts not present in uploaded materials.

| ID | Impact | Open item / exact question | Safe interim assumption | Who resolves / gate |
|---|---|---|---|---|
| D01 | BLOCKING FOR DOING | Which OS/version must installer support first? | Browser-local Ready only | Human chooses before native engineering |
| D02 | BLOCKING FOR DOING | Which legally usable real specialty repository is first, and are scripts/data exportable? | Curated synthetic fixtures only | Human + Codex repo audit |
| D03 | BLOCKING FOR DOING | Which direct model/region and provider data policy applies? | Simulated examples only | Human + security review |
| D04 | BLOCKING FOR DOING | Are cloud-managed tools/agent features actually in scope? | One direct LLM adapter only | Human PRD scope |
| D05 | BLOCKING FOR DOING | Where exactly may HAL read/write; is durable memory permitted? | Selected local files, no auto-upload | User consent / security |
| D06 | BLOCKING FOR CONTRACT | Engineering person-day rate, team, budget cap and desired dates? | No price/timeline claim | Human + vendor quote |
| D07 | BLOCKING FOR DISTRIBUTION | Is the imported repo's license compatible with repackaging? | No public distribution | Codex legal/license audit |
| D08 | NONBLOCKING READY | How many first users are available for 7-min UAT? | propose 5 testers, not yet interviewed | Human scheduling |
| D09 | NONBLOCKING READY | Which domain UI is the first pilot's defining specialty? | demo Research and Returns to test generality | Human feedback |
| D10 | NONBLOCKING READY | What does 'universal API' mean for unsupported providers? | typed ports, not universal raw key string | Engineer compatibility matrix |
| D11 | NONBLOCKING READY | Should version changes preserve last selected domain/feedback? | demo session-only | human accessibility/preferences |
| D12 | OPEN | Market substitution and support-cost baseline? | no ROI estimate | Product research |

## Contradictions preserved rather than silently resolved
- HAL v1 positions 1 specialist research app as primary MVM; v2 direct-fidelity hypothesis requires 2 *illustrative* specialties. This is a scope evolution, not evidence of deployment.
- Historic 虎翼成本数字包含不同版本、口径和币种；none are applied as HAL prices.
- 'Any API key' consumer language conflicts with real API families: model vs managed task vs channel and tool credentials; product will promise compatibility checking, not equivalence.
- 'No API key' Path A means no key entered into HAL; a separate IDE or code agent might still need model access.
