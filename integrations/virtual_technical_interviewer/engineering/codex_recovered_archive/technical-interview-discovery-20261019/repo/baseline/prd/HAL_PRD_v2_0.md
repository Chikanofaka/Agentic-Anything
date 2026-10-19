# HAL — Harness Activation Layer
## Experience-Refined Product Requirements Document · v2.0 · HAL-P2D-001

**Date:** 2026-10-14  | **Phase:** IDEA_RECONSTRUCTION → READY_FOR_HUMAN_UAT | **Decision:** HUMAN_GATE=PENDING  
**Prepared using:** `Need → PRD Reference-to-Template Compiler v2.0` (nine-step conversion + 30 generative operators + 32-section master), with v1 HAL PRD/MVM as baseline, not as prescriptive truth.  
**Source states:** `[USER_STATED]` user explicitly articulated; `[BASELINE]` observed in existing files; `[PROPOSAL]` design recommendation; `[ASSUMPTION]` unsourced scenario; `[ESTIMATE]` calculation pending input; `[VERIFIED_TEST]` new pilot test evidence recorded in receipt; `[OPEN]` no adequate evidence.  
**Sensitive material:** no API credentials or historical private firm data reproduced. **Caveat:** consumer demand, production model compatibility, and return on investment not externally established.

## 00. Document control, audience & decision
**Decision being requested:** approve whether to engineer a local-first HAL Shell and its v0 domain package contract *after* evaluating this PRD and the direct-fidelity MVM; public release is a separate decision. The readers are Product Owner, Codex engineer, technical/security reviewer, and prospective domain harness maintainer. Source priority: current HAL user Need > safely reusable methods abstracted from historical PRDs > baseline HAL v1 assumptions > new technical proposals. A discrepancy is not automatically resolved by taking the latest-looking artifact. Owner and actual budget require confirmation (`D-01`, `D-06`).

**Revision:** v1: shared onboarding, one research domain, simulated AI; v2: explicit Need-to-feature trace, cross-domain package swaps, executable deterministic domain core, common Shell boundary, alternatives/economics, regression evidence and self-recursive skill feedback. Owner approval: **PENDING**.

## 01. Executive decision summary — WHY / WHAT / HOW / VALUE / ACCEPTANCE
**WHY [USER_STATED]:** specialized GitHub harnesses provide deep methods but presume developer literacy; polished user-facing frontends may rely on provider-specific, nonportable AI integration. The costly translation between expertise, UI and model runtime is repeated across products.  
**WHAT [PROPOSAL]:** a *universal local-first HAL Shell* that loads a curated/versioned **Domain Harness Package (DHP)** and presents two deliberate paths: **A Developer** documentation + genuine export without granting HAL a key; **B Intelligent** model education + native secure credential flow + capability-aware domain-specific workspace and observable execution.  
**HOW:** declarative `harness.yaml`/JSON schema, package inspector, `feature_bindings`, model and tool/data adapters, permission/approval engine, task state/checkpoints and artifact ledger. A feature can be unlocked only when every required port and grant passes.  
**VALUE [HYPOTHESIS]:** reduce time-to-first-specialist-result and repeated engineering of onboarding, compatibility, trust and distribution.  
**COST [OPEN]:** engineering person-days, native packaging, external models/tools, maintenance, security verification; formula in §21, not historical quotes.  
**ACCEPTANCE:** demonstrate two distinct demo domain profiles through the **same shell** with real deterministic work, real Path A exports, a truthful simulated B preflight, denied incompatible cases and downloadable UAT; validate actual model-powered task only after DOING.

## 02. Problem evidence and Need trace
| Need | Actor/situation | Current substitute & friction | Desired measurable change | Evidence strength |
|---|---|---|---|---|
| N01 | Developer downloads GitHub harness | README/CLI/IDE skills must be interpreted manually | Complete documentation/export correctly used | User description, no population sample |
| N02 | Consumer wants specialized result | Generic chat UI or difficult repo | Unassisted route to task, consent, result | User description |
| N03 | Maintainer adapts next harness | Rebuilds auth/onboarding/runtime by hand | Faster *second* package integration | Product hypothesis |
| N04 | Security owner reviews model+tool access | Unsafe key input, untyped data privileges | No leaked key or unauthorized effect | Engineering threat hypothesis |
| N05 | Product Owner approves work | Beautiful mockup with nonfunctional engine | Transparent working/simulated boundary + UAT | Existing MVM observation |
| N06 | PRD compiler is reused | Generic template may omit project-specific decisions | 32 specific sections + exact trace/negative tests | User request + skill contract |

**Unverified:** prevalence, willingness to pay, alternative preference, actual integration duration and error frequency. Acquisition plan: 3 developer interviews, 3 consumer walkthroughs, 2 source repo audits, baseline comparison using A0 GitHub/IDE (proposed sample sizes, not completed).

## 03. Business strategy and product definition
**Position:** domain-independent bridge from a maintainable specialist harness to a predictable, controlled, user-ready local experience. Do **not** sell “any API key activates any GitHub app” as a feature. The differentiator is the domain-action binding contract and coherent dual-path experience.  
**Strategic assets:** package specification, curated adapter registry, permissioned runtime, reusable onboarding, measurable integration test suite and trustworthy execution receipts.  
**Alternatives:** A0 Github README-only; A1 bespoke domain app; A2 hosted universal launcher; A3 generic chat overlay. §24 compares trade-offs and falsifiers.

## 04. Goals, metrics and falsifiers
| Metric | Unit/cohort/period | Baseline | Proposed pilot decision threshold | Proof method |
|---|---|---|---|---|
| Path A export completion | % new unassisted testers in 7-minute session | OPEN | ≥4 of 5 (EXPERIMENT TARGET) | recorded user attempt, intact ZIP |
| Path B comprehension | % correctly distinguishing model vs tool permissions | OPEN | ≥4 of 5 | two-question teach-back |
| Valid first deterministic result | % of MVM first-time testers | OPEN | ≥4 of 5 | real downloadable domain result |
| Second-domain integration effort | engineer-hours | OPEN (bespoke baseline to measure) | ≥25% lower than bespoke, provisional | timed paired engineering exercise |
| No unauthorized external action | count across negative automated fixtures | expected 0 | exactly 0 | policy integration tests |
| User trust clarity | 1–5 Likert, cohort and date recorded | OPEN | median ≥4 | UAT questionnaire |

**Falsifiers:** Path A ZIP cannot run as documented; consumer confuses simulation for actual inference; second domain needs HAL core rewrites; first meaningful task is no easier than repository/IDE baseline; permission bypass. These targets are **pilot thresholds**, not achieved product performance.

## 05. Target users, stakeholders and responsibilities
| Role | JTBD and ownership | Decision permissions |
|---|---|---|
| Nontechnical domain user | complete specialized tasks after understandable onboarding | grant own provider and selected-file access; approve writes |
| Developer user | inspect, export, install and modify specialist package | download authorized source, run own IDE/model host |
| Domain maintainer | publish correct manifest, domain UI, tools & references | propose/maintain domain package; not grant customer privileges |
| HAL runtime maintainer | keep shell, adapters and policies compatible | ship signed updates after review |
| Product Owner / Human Gate | prioritize, decide scope, evaluate UAT | DOING / MODIFY / PARKED / BLOCKED; publication separately |
| Security/QA reviewer | threat model, red-team negative tests, test receipts | block release on credential or privilege failure |

**Initial account system:** single-user local runtime, no mandatory hosted account. Enterprise team roles and per-tenant access are **N/A for first MVP** except local OS identity and file consent; add RBAC only when a validated multi-user Need exists.

## 06. As-is journeys and bottlenecks
**A0 developer:** search GitHub→download ZIP→interpret README→resolve dependencies→configure IDE/model host→possibly discover missing files→try task. Bottleneck: unclear packaging completeness and which model/tool credentials belong to which program.  
**A0 consumer:** find polished app→click feature→learn backend is missing/provider-specific→try unrelated API key→fail or resort to generic chatbot. Bottleneck: no explicit capability readiness or permission story.  
**Maintainer:** rebuild home, docs, onboarding, connectivity, billing/key guide, run states, logging for each domain. Bottleneck: duplicate code and uneven safeguards. **Baseline time/defect measurements remain OPEN.**

## 07. Future-state service blueprint
**Shared entry:** Open signed local app → inspect verified domain package metadata → choose A or B; return/switch without reinstalling.  
**A:** `WELCOME → DEVELOPER_README → REQUIREMENTS → PACKAGE_TREE → DOWNLOAD_SOURCE → IDE_HANDOFF`; invalid/incomplete archive must be blocked with defect report.  
**B:** `WELCOME → DOMAIN_PREVIEW → KEY_ACADEMY(optional) → PROVIDER_SELECT → CAPABILITY_PREFLIGHT → NATIVE_BROKER_CONSENT → DOMAIN_WORKSPACE → TASK_EXECUTION → REVIEW/EXPORT`; user must distinguish sandbox simulation from real connection.  
**Recovery:** `UNSUPPORTED_PROVIDER`, `MISSING_DATA_GRANT`, `INVALID/EXPIRED_KEY`, `QUOTA_EXHAUSTED`, `PACKAGE_INVALID`, `RUN_FAILED`, `APP_CLOSED` are distinct states, each with next action. Completion is a verified artifact, not merely a chat message.

## 08. Scope, release stages and exclusions
**Ready v2 in scope (this package):** interactive offline browser-based shell, 2 seeded domain package profiles, developer README/package export, four-stage Key Academy, simulated preflight, realistic capability registry, real deterministic tasks (research margin and returns triage), exported source/report/diagnostics/feedback, approval/trust demonstrations, quality receipts.  
**Doing P0 after consent:** native secure credential broker, model inference adapter, typed local tools, manifest validation, durable run loop, real domain task and source-grounded artifact; instrument two real domain repos.  
**Post-MVP P1:** robust library import, signed extension registry, more providers, MCP, scheduling, enterprise RBAC if evidenced.  
**Excluded:** arbitrary untrusted repo auto-execution, universal provider semantics, fake “any key”, credit reselling, financial advice, 24/7 operation when device off, scraped private datasets, publication without authorization.

## 09. Capabilities & functional requirements
Every feature is further specified with input/output, negative case and test ID in `UAT_MATRIX.md`.
| FR | Priority | Scenario/actor | Deterministic & adaptive contract | Data/permission | Acceptance ID |
|---|---|---|---|---|---|
| F01 | Must | User starts shell | choose A/B, back & switch | no secrets | T01 |
| F02 | Must | Maintainer loads domain | versioned manifest maps `id/title/exports/features/ports` | signed/curated only in v0 | T02 |
| F03 | Must | Developer reads domain | README relevant to selected domain and actual package tree | approved source | T03 |
| F04 | Must | Developer exports | real complete ZIP, no credentials | selected package | T04 |
| F05 | Must | Consumer learns BYOK | 4 Key Academy lessons with completion checks | no billing/password collection | T05 |
| F06 | Must | Consumer selects model port | capability check, unsupported direct/managed port blocked | no key in MVM | T06 |
| F07 | Must | Consumer sees specialized workspace | two unique tasks & distinct labels under same shell | fixtures only | T07 |
| F08 | Must | User runs arithmetic/workflow | locally computed deterministic result + generated report | validates inputs | T08 |
| F09 | Must | User requests AI insight | SIMULATED in Ready; in Doing: genuine bounded domain tool call | broker permissions | T09 |
| F10 | Must | User probes risks | feature readiness matrix with missing ports and grants | denies unavailable | T10 |
| F11 | Must | User exports | report, manifest, diagnostics, developer ZIP, UAT feedback | approved files only | T11 |
| F12 | Must | Product Owner tests | Human Gate scorecard / decision receipt | local feedback | T12 |
| F13 | Must | User encounters error | invalid input, unsupported provider, disconnect & recovery | no side effect | T13 |
| F14 | Must/Doing | Developer connects key | native secret store, no raw browser key handling | OS broker + scoped refs | T14 |
| F15 | Must/Doing | Agent acts | max steps/spend, checkpoint, human write gate, provenance trace | scoped tools | T15 |
| F16 | Should/Doing | Maintainer integrates 2nd repo | same manifest and HAL core | license/auth audit | T16 |

**Domain binding invariant:** `UI_CONTROL → FEATURE_ID → REQUIRED_CAPABILITIES → BOUND_TOOL/WORKFLOW → RESULT_SCHEMA → RECEIPT`. UI must not show “enabled” solely because a string resembling a key was entered.

## 10. Information architecture and UX
Seven to nine practical surfaces: Home/choose path, Developer Readme, Developer Package, Key Academy, Activation, Domain Studio, Compatibility/Trust, Run/Outputs, Human Gate. Navigation always includes package name, selected mode, current demo/real status, cost warning and restart. Default path is exploration rather than immediate credential solicitation.  
**UX principles:** progressive disclosure; inspect before connect; teach by doing; domain-native controls; avoid implying chat is the whole product; explicit real/simulated status next to every important effect. Keyboard/contrast/small-screen target AA standards (requires future accessibility audit).  
**Magic moment:** switch from `Research Diagnostics` to `Returns Operations` in the same HAL shell and see task controls, README, binding matrix and export package update **without reloading or changing shell logic**; complete a different real deterministic task. Target discovery within 60–120 seconds (hypothesis).

## 11. Account, identity and permission design
**Ready:** browser-local sample state; no user authentication, API keys, OAuth secrets or real private documents.  
**Doing:** local OS identity + native credential vault; pass only short-lived credential reference to a trusted native adapter; least-privilege explicit directory/file access; tool-specific user grants and per-action confirmation for publishing/email/deletion or paid jobs; capability and permission deny list cannot be overridden by prompt. Logs redact secrets and personal paths.  
**Matrix:** consumer may read selected workspace/write to user-approved output path; domain package may request but never grant tools; model receives only authorized context; plugin cannot read arbitrary filesystem; telemetry opt-in.  
**Negative tests:** another user's file path forbidden; prompt injection asks to upload key→blocked; export scan must not contain raw keys or historical confidential reference content.

## 12. Data inventory and information lifecycle
| Entity | Origin/status | Minimum fields | Trust boundary | Retention |
|---|---|---|---|---|
| Domain package manifest | Maintainer/versioned | id/version/entrypoint/domain/actions/ports/digest | untrusted until verified | installation life |
| Domain Skills and code | Maintainer | paths/licenses/dependencies/version | executable quarantine | until uninstall |
| User task data | User-selected fixture/real | value/unit/period/provenance | local chosen paths | user managed |
| Provider credential reference | Native OS broker in Doing | provider/ref/scopes/created/revoked | secret not serializable | until revoke |
| Run event/receipt | HAL runtime | stage/tool/effect/status/est cost, no secrets | local runtime | user-configurable |
| User UAT | User-authored | scores/decision/comments/version | local export (demo) | user choice |

**Source integrity:** validate declared files exist, hashes and manifest against actual exports. Reject `../` traversal, symlink breakout, hidden secret inclusion, unsigned executable packages (Doing). Avoid auto-embedding entire domain repo in model context.

## 13. Data governance and trust boundaries
Trust levels: `[trusted signed HAL code]`, `[curated but separately verified domain package]`, `[untrusted imported references/web/documents]`, `[private user data]`, `[native credentials]`. Boundaries are enforced in runtime, **not** by model self-instruction. A document claiming higher priority cannot grant permissions. Each data flow logs purpose, data class, tool grant and provenance where appropriate. No source enterprise financial/customer documents distributed in public artifacts. Local execution still transmits prompts/context to a remote model when explicitly authorized.

## 14. Three-layer architecture
**Application:** shared native shell/webview; onboarding A/B, developer docs, Academy, domain UI, trust panel, approvals, output/UAT.  
**Logic:** package inspector/parser, manifest/capability resolver, feature binding graph, mode FSM, provider adapter family (direct model / managed agent / embedded channel), typed tool/data gateway, permission evaluator, model loop with step/budget ceilings, local run ledger.  
**Data/infrastructure:** domain archives, user-selected files, native OS vault, local SQLite state, approved remote model/tool endpoints, output workspace.  
**Contract:** `inspect(Package)→CompatibilityReport`; `selectDomain(id)→DomainUIModel`; `preflight(provider,domain)→Availability[feature]`; `run(goal,grants)→events/artifact`; `export(kind)→validated bytes`. All outbound data flows require explicit destination and authorization. In Ready MVM, preflight and model execution are simulated; local deterministic operations actually work.

## 15. Domain knowledge and specialist methods
HAL contains no investment assumptions or healthcare domain procedures by default. The domain package owns its validated methods, inputs/outputs, quality rules, evidence standards, and specialty UX.  
**Demo domain 1 Research Diagnostics:** formula `(revenue − cost)/revenue`; valid revenue>0 and cost≥0, with chosen abstract unit; output profit and margin, labeled not investment analysis.  
**Demo domain 2 Returns Operations:** classify returned packages using explicit condition/receipt/age rules, producing deterministic triage category. No real customer personal data.  
**Domain extension principle:** independent technical capability and review may be required for regulated decisions; a domain package can declare an expert challenger/review gate where justified, not an obligatory five-agent pattern.

## 16. Business workflow / agent orchestration
**Mode FSM:** `UNCONFIGURED → PATH_SELECTED → READINESS_CHECK → READY → RUNNING → (WAITING_APPROVAL | COMPLETED | FAILED | CANCELLED | QUOTA_BLOCKED)`; with `DISCONNECTED → RECONNECT_REQUIRED`, `PARTIAL_OUTPUT` preserved if permitted.  
**Node contract:** node ID; actor; trigger; input schema; deterministic operation; optional LLM skill; allowed tools; timeout; output schema; verification gate; human approval condition; next-state, persistence and error policy.  
**Execution proof:** Doing acceptance requires at least one **actual model-request → authorized tool-call → returned tool result → specialty artifact** with a receipt and a negative denied tool path. The Ready MVM never claims this completed.

## 17. Vendor/model/API and tool dependencies
| Port | Function | Required capabilities | Distinct auth? | Ready / Doing |
|---|---|---|---|---|
| LLM_DIRECT | generate/stream/tool calling | requested model features | provider API key | simulated / implement one |
| MANAGED_AGENT | submit task, poll, artifacts, approvals | provider task semantics | account and task rights | incompatible demo / future |
| EMBEDDED_CHANNEL | hosted third-party agent UI | channel SDK/session | provider channel token | not demoed / later |
| DATA_FEED | licensed query or private DB | rights/source/schema | distinct from LLM | fixtures / optional |
| TOOL_API | local filesystem, web, GitHub | typed effects/consent | per tool/provider | deterministic fixtures / guarded |

Do not infer real capability from “OpenAI-compatible” HTTP shape. Provider pricing, geographic constraints, rate limits, tool support, data processing and credential storage rules require current official verification when Doing begins.

## 18. Memory, context, edits and citation
Separate transient turn context, domain asset/version history, run-state checkpoints and opt-in user memory. Every persisted preference has visibility/export/delete controls. For sources/reports record document ID/version/claim-to-citation links and freshness as required by specialty; no phantom citations or invented retrieved knowledge. In the MVM, fixture output and on-page choices are session-only; do not claim persistent learning or true AI memory. Adaptive explanation must never silently rewrite deterministic calculations.

## 19. Nonfunctional requirements
| Attribute | Engineering target and validation (proposed) |
|---|---|
| Security | zero credential value in renderer/log/export; negative path/permission tests; external writes gated |
| Installability | signed installers for a confirmed OS matrix; clean-machine install without Python/Node terminal |
| Availability | local app works for deterministic functions offline; AI requires network; explicit offline status |
| Performance | demo UI navigation immediate; Doing key/preflight bounded with visible timeout/retry |
| Reliability | interrupted/cancelled tasks have explicit state and error receipt; no fake success fallback |
| Portability | 2 dissimilar audited real domain packages through unchanged HAL core |
| Observability | structured per-run events, provider usage estimate (not billing truth), no secrets |
| Accessibility | keyboard navigation, focus state, readable contrasts, screen-reader labels audited |
| Maintainability | schema-versioned manifests, tests for compatibility/upgrade, rollback plan |

## 20. Key scenarios and Mockup specification
**Golden G1 / Developer:** select Returns Operations→Developer→read accurate README→download valid `returns-harness.zip`→inspect source and run local CLI with documented fixture (manual command outside UI). Pass if all files exist and output matches spec.  
**Golden G2 / Consumer:** select Research Diagnostics→Intelligent→complete Key Academy→simulate OpenAI preflight→domain Studio→enter revenue 1500 and costs 900→real 600 profit, 40.0% margin→download Markdown; AI explanation always tagged SIMULATED.  
**Golden G3 / Direct product:** switch to Returns Operations in same running shell→different controls, README/ZIP/binding matrix→choose `sealed / proof yes / 5 days`→deterministic returns triage and downloadable decision note.  
**Negative N1:** choose Manus for direct model port→`MANAGED_AGENT_PORT_MISMATCH`, cannot simulate direct-provider activation.  
**Negative N2:** revenue=0 or costs<0→validation error, no report until correction.  
**Negative N3:** disconnected AI→AI interpretation button disabled, deterministic tasks still work.  
**Negative N4:** attempted API-key input into static demo→no field; security messaging directs future native broker.  
**Creative constraints:** 3–5 teaching missions, at least 5 distinct interaction types, visible objective/progress, 4 output actions, real cross-domain action, explicit recovery and Human Gate export. `MVM_SPEC.md` contains UI inventory.

## 21. Economics — cost structure
**Do not borrow March enterprise PRD amounts or old rate assumptions.** Normalize `period`, `currency`, `geo`, `unit`, `cohort`, `price source/date`, `license`, `range` and `confidence` before pricing.  
**Build = Σ_i(person_days_i × blended_day_rate_i) + security + installer + QA + contingency.** Candidate work packages: package inspection & manifest (D1), front-end shell (D2), native secret broker (D3), model adapter & loop (D4), tool policies (D5), domain integrations (D6), packaging/security/test (D7). Each D_i and rate is `TO_VALIDATE by Codex audit`.  
**Recurring per period = model input tokens × provider input rate + output tokens × output rate + provider tool premiums + licensed sources + support + updates + infrastructure (if any).** BYOK charges user directly for provider inference; HAL may still incur maintainer support and release costs.  
**Sensitivity:** low/base/high usage and person-days, separated fixed vs variable cost. No “$0 to run” claim without evidence; no vendor price is represented as a quotation.

## 22. Business value and ROI
| Expense/constraint | Value candidate / measurement |
|---|---|
| Build and maintenance person-days | reusable second-harness integration engineering-hours saved vs bespoke (measure paired trial) |
| API fees paid directly by user | measurable valid specialty outputs and user-reported task time vs provider spending |
| QA, signing and dependency upkeep | fewer broken installs; security incidence and remediation speed |
| Provider/model volatility | ability to switch compatible model with verified outcome (not merely key-format support) |
| Key Academy/onboarding effort | better first-run completion and comprehension, lower support need |

**ROI only if attributable benefits verified:** `(validated economic benefit − lifecycle cost) / lifecycle cost`; separately report qualitative strategy/trust. Time redeployed is not automatic payroll saving. Pilot business case remains `OPEN` until measured.

## 23. Supplier scope / request for proposal
Codex implementation response must include: source repo/license audit; package & manifest validation; component boundary; tool/data dependency inventory; proposed native key store and threat model; provider adapter selection; person-day range by work package with assumptions; real trace and one negative case; test/mocking boundary; clean install matrix; exported artifacts; rollback and release plan; exclusions; IP/security commitments; acceptance evidence. A mockup or a successful LLM response is not payment/acceptance by itself.

## 24. Risks, assumptions and alternatives
| Risk / alternative | Trigger | Mitigation / test | Owner/status |
|---|---|---|---|
| Existing IDE/GitHub workflow already sufficient | developers prefer no launcher | unassisted baseline comparative task | Product / OPEN |
| Any arbitrary repo cannot run | missing deps/unsafe code | curated first, parser and sandbox roadmap | Engineering / PROPOSAL |
| Provider key incompatible or insufficient | managed Agent≠model; missing data rights | typed port registry and blocked state | Engineering / PROPOSAL |
| Secret leak | frontend/logger/export includes raw value | native store + scanning + no demo key field | Security / MUST |
| Decorative assistant | model cannot invoke specialist tool | require end-to-end domain workflow in Doing | Product+QA / MUST |
| Scope creep / impossible cross-domain promise | every new domain needs special runtime change | explicitly measure second-domain adaptation | Engineering / OPEN |
| Historical costs imported | source cases in different periods/currencies | use formulas + fresh quotes only | Product / MUST |
| Consumer privacy expectations wrong | data leaves local device for model | consent screen and data flow receipts | Security / MUST |
| **A0 GitHub only** | no common shell or B | lower costs, weaker consumer UX | alternative retained |
| **A1 bespoke app** | high specialty control, duplicated platform work | baseline for reusability trial | alternative retained |
| **A2 cloud launcher** | always-on convenience, hosted data/ops | future option, rejected for current local-first Need | alternative retained |

**Strongest objection:** a shared abstraction may burden niche specialists with interface limits; kill or narrow product if integration hours/quality don't beat a bespoke implementation.

## 25. Quality gates and acceptance testing
**Ready gates:** (Q1) seven-plus functional views; (Q2) two profiles same shell; (Q3) real deterministic specialist outputs; (Q4) real ZIP exports; (Q5) incompatible provider blocked; (Q6) explicit REAL/SIMULATED labels; (Q7) UAT JSON; (Q8) 5–7 min opening & human script; (Q9) all file links and archive contents verified; (Q10) invalid case/recovery; (Q11) package integrity/no secrets; (Q12) annotated honest browser-test debt.  
**Doing gates:** actual OS vault, network API call, allowed tool and denied tool, real report, consent receipt, model budgets, crash/disconnect behavior, clean install, actual two-repo integration; independent security review before distribution.  
**Human Gate:** DOING / MODIFY / PARKED / BLOCKED; default **PENDING**. Artifact delivery is not automatic approval or public release.

## 26. Milestones, dependencies and resource plan
| Phase | Exit deliverable | Blocking dependency | Proposed role | Time/effort status |
|---|---|---|---|---|
| READY v2 (now) | PRD, MVM, trace, UAT, source packs | current Need + reference baseline | Product / MVM engineer | produced; human test pending |
| GATE | Human UX findings + explicit verdict | user walkthrough | Product Owner | OPEN |
| DOING-1 | license audit, manifest spec, local broker and one model port | approved scope, target OS and provider | Codex + security | estimate pending |
| DOING-2 | one real specialist model-tool-run; denied writes | working tool contracts/credentials | Codex + QA | estimate pending |
| DOING-3 | second real domain + unchanged shell proof | domain repo rights and access | Codex + reviewer | estimate pending |
| REVIEW | signed installer, clean-machine test, release checklist | all gates + separate publication consent | QA + Product | not authorized |

Parallel activities (README/spec, UX, fixtures) may start after Need capture; credential handling and arbitrary code may not precede trust/permission design. This is a **dependency-first plan**, not an invented delivery date or supplier commitment.

## 27. Operations and change management
Version HAL core, manifest schema, provider guides and domain packages separately. Registry records compatibility matrix, migration notes, rollback, deprecation grace, blocked extension. Run ledger contains nonsecret state/usage estimates; output artifacts remain local or at explicitly authorized destination. Users can export/delete their tasks and disconnect provider; declining telemetry doesn't remove deterministic functionality. Incident procedure: invalidate exposed key, disable extension, preserve redacted diagnostic and publish fixed version only after review.

## 28. Decision governance and signoff
| Decision | Options | Evidence needed | Approver | Default until resolved |
|---|---|---|---|---|
| D01 First supported OS | macOS / Windows / both | target testers, signing cost | Human | no assumption |
| D02 Which real domain repo first | Research vs MemoriGPT vs other | license, completeness, authorized data | Human+Codex | curated sample only |
| D03 Model provider and region | supported providers | real feature compatibility and privacy | Human+Security | mock simulation |
| D04 Runtime stack | Tauri/Rust vs other local patterns | threat model, team skills, estimates | Codex recommends/Human approves | architecture option only |
| D05 Source/private permissions | local-only, optional connectors | data inventory & owner grants | Security+Human | deny by default |
| D06 Budget and sprint scope | narrow / expanded | days×rates & resources | Human | not approved |
| D07 Public GitHub release | yes/no | license, secure code, QA | Human | NO |

No implicit approval from an excellent score or mockup. Change log tracks decisions separately from proposed implementation.

## 29. Appendix — Traceability and source map
Core source lineage: `NEED_NORMALIZED.md` (N01–N06) → `TRACEABILITY.csv` → `UAT_MATRIX.md`; previous `HAL_PRD_v1_0.md` and `ready-mvm/index.html` are BASELINE, not proof of live AI. Generative method from v2 `SKILL.md`, `01-CONVERSION_KERNEL.md`, `04-GENERATIVE_OPERATORS.md`, `01-MASTER_PRD.md`, specialized UAT/role/data/cost templates. Historical 虎翼 PRDs/diagrams abstracted into reusable principles (WHY/WHAT/HOW, scope/security, cost-value and acceptance) but their company actors, dollar figures, provider selections and sensitive data are not copied as new truth. The detailed `SOURCE_AND_DECISION_LEDGER.md` distinguishes these states. No market study or live model test has been performed in this Ready stage.

## 30. Professional slide/diagram blueprint
For review deck (not produced as an independent slide artifact): slide 1 Need/problem/status; slide 2 before-after user journey; slide 3 **shared shell + two domain packages and two paths** (arrows labeled data/permission); slide 4 typed model/managed-agent/tool connectors; slide 5 state/denied paths and secret boundary; slide 6 cost-value equation (zero fictitious estimates); slide 7 direct product MVM and demo test; slide 8 decision, blockers and next sprint. Each diagram must be convertible into implementation and acceptance contracts, not abstract decoration.

## 31. Engineering handoff and next learning experiment
**Pilot learning experiment now:** compare v1 and v2 MVM through one unassisted user run, observe whether domain-switch and capabilities are understood; collect exported JSON; record modifications.  
**Approved future engineering experiment (only after DOING):** import two legitimate nontrivial repositories, retain their distinct specialty tests, implement one real guarded model loop, measure adaptation hours and model-vs-tool capability mismatches.  
**Handoff:** `CODEX_HANDOFF.md` lists boundaries and QA evidence. **Skill self-recursion:** `PILOT_RECURSION.md` records v2 template failure modes, proposed patches and regression prompts; it must not rewrite evidence retroactively or claim the Skill is installed/updated.  
**Current verdict:** READY_FOR_HUMAN_UAT_WITH_DEBT; `HUMAN_GATE=PENDING`; engineering and public distribution NOT started.
