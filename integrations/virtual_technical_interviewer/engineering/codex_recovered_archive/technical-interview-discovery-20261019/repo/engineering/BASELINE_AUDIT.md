# HAL-P2D-001 implementation baseline audit

Audit date: 2026-10-16 (Asia/Shanghai). Human Gate: **DOING**. This audit records the untouched Sprint 0 baseline before Sprint 1 implementation. No provider, network, credentials, external writes or publication are authorized or needed.

## Sources reviewed

Read `AGENTS.md`, `README_START_HERE.md`, `status/HUMAN_GATE.md` first; then the v2 PRD, normalized Need, traceability CSV, UAT matrix, architecture options, CODEX_HANDOFF, PILOT_RECURSION, Ready HTML, runtime README/engineering/security/scope/decision docs, all Core modules, trusted adapters, manifests and tests. Historical PENDING labels in the PRD/handoff/MVM describe the Ready artifact; the current gate file and user instruction authorize bounded local DOING. Baseline artifacts and candidate Skill remain historical, unchanged.

## Executed evidence

`bash scripts/verify_local.sh` exited 0: **31/31 tests pass**, Research 1500/900 -> profit 600.0 and margin 40.0%; Returns sealed/yes/5 -> STANDARD_RETURN. Both receipts state DETERMINISTIC_OFFLINE, live_model_used=false, external_writes=false.

The script only printed the expected Manus denial, so a separate command was executed from runtime: `python3 -m hal_core.cli preflight --package fixtures/research --feature ai-interpretation --provider manus`. It exited **2**, status BLOCKED, missing_ports included MANAGED_AGENT_PORT_MISMATCH. It also incorrectly reported the available local calculator missing for the AI feature.

Actual interpreter: **Python 3.9.6**. Documentation requested 3.10+; passing on 3.9.6 is observed compatibility, not evidence of a tested 3.10+ support matrix. No interpreter/dependency was installed.

## Reality ledger

| Area | Baseline evidence and limits |
|---|---|
| REAL: shared Core | One CLI/inspector/resolver/engine dispatches two installed curated adapters; no core swap between domains. |
| REAL: specialist outputs | Margin formula and fictional returns policy execute deterministically. Synthetic teaching fixtures, not third-party domain validation. |
| REAL: boundaries | Tests reject known traversal, symlinks, common secret filenames, invalid inputs, unknown domains, spoofed local port and AI execution. Imported main.py is never executed. |
| REAL but partial: package inspection | Root directory/ZIP, file checks, SHA-256 content digest, permissions and a demo manifest. Digest is not publisher authentication; schema is not strict despite documentation wording. |
| Path A | README, AGENTS, Skills, source entrypoints and downloadable source ZIPs exist. The Ready HTML exposes IDE handoff; runtime source import remains data-only. No new browser/clean-machine validation in this audit. |
| Path B | Ready HTML has meta-onboarding, Key Academy, provider education and different domain controls. HTML deterministic functions work by separate JavaScript; runtime is not wired to that UI. Provider activation/insight are SIMULATED. |
| ASSUMED / missing | Native authenticated bridge, OS vault, signed distribution, license/publisher verification, durable agent loop, actual provider capabilities, real external domains and market/effort measurements. |
| OUT_OF_SCOPE | Live credentials/inference, paid calls, external data, network services, external writes, publishing and Skill promotion. |

## Reproduced defects and implementation decision

Read-only review plus temporary synthetic attack fixtures established:

1. Unknown manifest/permission fields, duplicate JSON keys, NaN, and nested secret-shaped fields pass inspection. No explicit host compatibility or typed tool input/output contracts.
2. Common GitHub wrapper ZIPs fail because harness.json must be at archive root. Raw aliases a//b and a/./b pass; ZIP directory entries bypass symlink validation; .ENV.production passes filename checks.
3. A symlink package root is accepted; directory FIFOs are silently omitted. CRC-corrupt ZIP raises raw BadZipFile rather than a stable structured failure.
4. The resolver keys local tool lookup by feature ID, so an AI feature cannot recognize its existing specialist tool independently. Registry tuple lacks permission and input/output metadata.
5. Research revenue=10**400 raises uncaught OverflowError; revenue=1e-308/cost=1e308 yields SUCCESS with margin_pct=-inf. These are synthetic test values, not user/business data.

Smallest coherent Sprint 1 slice: strict versioned `hal-domain/v1`; explicit read-only normalization of existing `hal-demo/v0.2`; bounded data-only directory/ZIP inspection including one unambiguous GitHub top folder; typed installed tool contracts, capability diagnostics and effect denial; input/output checks; security/regression tests; executable verifier assertions and receipts. Keep consumer UI bridge separate until authentication, transport and native platform are designed. No decorative chatbot and no PRD rewrite.

## Requirement trace

F02/T02: schema, compatibility and package import; F03/T03 and F04/T04: preserve referenced developer assets and reject unsafe archives (no new exporter); F06/T06: direct/managed capability denial; F07/T07 and F08/T08: two distinct tools through shared Core; F10/T10: truthful readiness and permissions; F13/T13: safe failure without stale result. F14–F16 remain unimplemented. F01/F05/F09/F11/F12 remain baseline UX/simulation or partial existing exports, not newly integrated runtime features.
