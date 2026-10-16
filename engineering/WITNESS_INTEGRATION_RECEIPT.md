# HAL × Witness Loop implementation receipt

Date: 2026-10-16, Asia/Shanghai. Stage remains **DOING**. This application increment follows the completed [Sprint 1 receipt](SPRINT1_RECEIPT.md), whose audit/results remain historical and unchanged.

## Delivered result

Built a local Mac application that applies HAL to the user-supplied Witness Loop domain: native host, specialized game UI, hard plot transitions, attributed saved memory, developer pathway and native OpenAI request adapter. The original simulation is preserved unchanged. This is a working local engineering prototype, not a published plugin, portable installer or universal harness SDK.

The user's clarified vision and remaining acceptance requirements are in [HAL_WITNESS_TYPE_B_PRD.md](HAL_WITNESS_TYPE_B_PRD.md). Read the [launch guide](../integrations/witness_loop/README.md) to play. Built application: `integrations/witness_loop/dist/Witness Loop.app`. Complete developer source ZIP: `integrations/witness_loop/dist/HAL_Witness_Loop_Source.zip`, produced from explicit source roots by `scripts/package_witness_source.py`; it excludes session data, caches, credentials, build products and logs.

## Ground truth and verified evidence

Before this increment, `bash scripts/verify_local.sh` passed **136 tests**, the Research/Returns CLI results and Manus denial. Sprint 1 source was already committed locally. The supplied Drive bundle was inspected as data: all ten preserved files match its ZIP bytes; SHA-256 and source-review findings are recorded in [SOURCE_PROVENANCE.md](../integrations/witness_loop/SOURCE_PROVENANCE.md). No original file was modified or used as executable imported domain code in the new app.

Environment observed: macOS arm64, Python 3.9.6, Swift 6.1.2 compiler with Swift 5 mode and macOS 12 deployment target. No dependencies were installed. The target does not establish compatibility with every macOS 12+ machine; only this Mac was exercised.

| Verification | Executed result |
|---|---|
| `bash scripts/verify_witness_local.sh` | Exit 0; **220/220 Python tests**, original CLI golden outputs/denial, app build and **41/41 native tests** |
| `WitnessLoop --ui-self-test` inside the built app | Exit 0; **9/9 actual offline JS → native → Core → rendered UI checks**, isolated test directory, activation disabled |
| `native/check_unicode_bounds.py` | Synthetic near-limit save 1,999,999 bytes; conservative ASCII-expanded export 6,915,446 bytes, below native 8 MiB bound; actual worker now emits UTF-8 |
| `git diff --check` | No whitespace errors |
| Source ZIP verification | CRC/file-list/byte equality checked after packaging; no session data included |

Python suites: original `test_hal` 31, package security 43, schema 29, capabilities **27**, CLI 9, Witness domain **39**, interactive host **42**. Total **220**. Native tests use `URLProtocol` synthetic responses, not an actual API connection. GUI checks traverse real private pipes and verify the truth ending, developer assets, literal rendering of an HTML-shaped player name, CSP and absence of a renderer credential field. A screenshot was captured and inspected at `integrations/witness_loop/.build-cache/witness-ui-smoke.png`. GUI checks are bridge/DOM integration evidence, not a human gameplay study or native credential/export-dialog UAT.

Raw local logs: [combined regression/build log](verify_witness_local.log) and [GUI integration log](verify_witness_ui.log). Logs are ignored by Git. The first full regression after adding Witness exposed one stale expected error code: `TOOL_API` now has a reviewed binding. The updated test still requires an unmatched domain/tool to be denied, and new tests verify actual Witness dispatch and blocked CLI model activation. Final results above come from the complete rerun, not a sum of diagnostic runs.

## Behavior demonstrated

- Research still returns profit **600.0**, margin **40.0%** for revenue 1500/cost 900; Returns still returns **STANDARD_RETURN** for sealed/proof yes/5 days. Both remain deterministic, with no live model or third-party write.
- Witness's `witness-step` uses the same inspected package registry, typed capabilities and input/output validation as those domains. Unknown/mismatched tools and unavailable effects remain blocked. Native interactive activation is separate from offline CLI preflight; the CLI does not claim verified model access.
- Explicit protection pledge → phone question → remembered commitment and call evidence → scene progression → valid clock/call contradiction → truth verdict works through the actual app. Domain tests cover partial and false-accusation endings, locked clues, premature verdicts, arbitrary/repeated links, model topic routing and negated/conditional promises.
- Casual conversation uses no plot-action budget. Six plot actions remain bounded. Persona context omits locked case facts and selects bounded relevant memories/history. Structured player statements remain distinct from admitted case facts; model prose cannot directly write evidence or memory claims.
- Atomic session saves and validated restore preserve conversations, profile, commitments, clues and receipts. Failed/invalid replies or writes leave committed state intact. Stale/replayed commits and interleaved scene changes are rejected. Reset/forget invalidate pending drafts; full forget removes the active profile and case, not prior export copies.
- Native-only credential UI, fixed provider endpoint, strict schemas, bounded requests, no redirects/retries, duplicate-key/refusal/error/oversize handling and secret-echo rejection are implemented. The renderer cannot submit keys, endpoints, file paths or fabricated model results. No public/local HTTP listener is involved.
- Long Unicode histories now fit a coherent save/transport budget. The host tests restore and export a valid save larger than 1 MiB through the actual worker process. Failed native commits clear pending drafts before unlocking; native confirmation is wired for the UI's delete action.

## Changed files

| Files | Purpose |
|---|---|
| `runtime/hal_core/registry.py`, `ports.py`, `schema.py` | Reviewed Witness tool/lifecycle binding and typed `narrative_state` capability; curated TOOL_API dispatch |
| `runtime/trusted_adapters/value_contracts.py`, new `witness.py` | Strict domain input/output/state contracts, identity, scene/evidence rules, three endings, context construction and memory projection |
| New `runtime/hal_core/interactive.py` | Shared private stdio host, fixed-domain inspection, staged turns, revision/provenance receipts, atomic bounded storage, restore/export/delete |
| New `runtime/fixtures/witness/` | Versioned manifest, README, AGENTS, domain Skill and inert source marker for both pathways |
| `runtime/tests/test_capabilities.py`; new `test_witness_domain.py`, `test_interactive.py` | 84 added regression/security tests relative to Sprint 1; prior checks preserved with updated TOOL_API expectation |
| New `integrations/witness_loop/native/` | AppKit/WKWebView host, native activation/export/confirmation, fixed OpenAI adapter, strict JSON parser, worker transport, mocked tests, GUI checks and boundary notes |
| New `integrations/witness_loop/ui/` | Chinese onboarding, persona game, evidence board, memory controls, truthful modes, developer pathway; no HTML interpolation of dynamic text |
| New `integrations/witness_loop/source/` | Ten unchanged user-supplied reference files |
| New `integrations/witness_loop/README.md`, `SOURCE_PROVENANCE.md` | Launch, developer handoff, original-source hashes and adaptation record |
| New `scripts/build_witness_mac.sh`, `verify_witness_local.sh`, `package_witness_source.py` | Local app/source packaging and reproducible offline verification |
| `.gitignore`, `README_START_HERE.md`, `runtime/README.md`, `runtime/docs/SECURITY_AND_LIMITATIONS.md` | Exclude private state/cache; link current increment and distinguish historical boundaries |
| New `engineering/HAL_WITNESS_TYPE_B_PRD.md`, this receipt | User-vision addendum, acceptance/requirement trace, evidence and remaining work |

The baseline PRD/MVM, original Research/Returns fixtures, Sprint 0/1 receipts, Human Gate file and unpromoted Skill candidate remain unchanged. No commit, push, publication, deployment or external-account write was performed in this increment. Google Drive was used only to retrieve the user-provided references; OpenAI documentation was read to implement the API contract.

## Reality and limits

**REAL / VERIFIED LOCALLY:** shared deterministic architecture, specialist state changes, persistence and memory provenance, game UI, native/private bridge, package validation, mock provider transport/parser tests and offline full-flow checks.

**SIMULATED:** no-key character language; synthetic provider responses in tests. Domain rules and saved state are real even when language is simulated.

**IMPLEMENTED, LIVE UNVERIFIED:** OpenAI topic/reply requests and native credential workflow. No real credential was accessed, entered or used; no billable provider call was made. LIVE_VERIFIED is only set in app code after a valid provider response, not by a test that assumes a key works. It means session response evidence, not a provider certification or guarantee of persona quality.

**NOT COMPLETE:** arbitrary harness embedding, generic multi-domain consumer shell, provider-independent live capability grants, Keychain persistence, signed/notarized distribution, bundled Python, second real external-domain validation, human UAT and production hardening. A random third-party credential is not automatically compatible with the fixed OpenAI endpoint.

Memory is bounded, plaintext and local; selected context is sent to OpenAI only during user-enabled requests. It is not perfect recall, encrypted-at-rest storage or guaranteed provider zero-retention. Native key memory is not guaranteed zeroizable. `external_writes:false` excludes third-party writes but does not deny local session saves. Receipts rely on the trusted parent and local files, not cryptographic attestation. Single app instance per checkout is assumed; concurrent session writers are unsupported. Unsigned trusted local code is not an OS sandbox. Source provenance/license verification and model narrative consistency remain open.

## Next implementation steps

1. Human local playthrough of the current offline build and native panels; then, when desired, enter an authorized OpenAI key directly in the app and accept its bounded request consent. Validate actual model access, personality, paraphrases, nudges and cross-scene recall. Do not send a key through chat. This live acceptance cannot be claimed from mock tests.
2. Add reusable interactive action/profile contracts and provider capability grants; integrate a second real specialist domain without rewriting persistence, broker or model transport. Measure adaptation effort before claiming generalized embedding.
3. Package runtime dependencies, enforce single-session ownership, establish signed package/license trust and distribution signing, then test clean Macs and failure recovery. Add monetary budgets if a true currency ceiling is required.
4. Run the source PRD's human test (at least 3 of 5 users perceive memory and want to continue), plus adversarial persona/knowledge leakage checks. Expand content only after that evidence.

F01–F16 trace and acceptance boundaries are recorded in the [PRD addendum](HAL_WITNESS_TYPE_B_PRD.md). DOING remains approved; product Completion and publication remain unapproved.
