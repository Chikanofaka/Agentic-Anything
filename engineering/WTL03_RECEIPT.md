# WTL-029 v0.3 · engineering receipt

Implemented 2026-10-16–17 (Asia/Shanghai), in the existing HAL-P2D-001 checkout. Starting commit: `cf2b22f`. **Human Gate remains DOING; application prepared for human review.** No commit, push, deployment or paid gameplay API call was made. Player saves were not read, deleted or used in testing.

## Result and baseline comparison

The original OpenAI-capable native prototype already had genuine HAL state, six case-action rules, provider isolation, memory and three outcomes. Its UI was text-heavy; its original v1 state granted the clock immediately and ticket in Scene 2. Updating Markdown alone did not prove runtime character loading. Baseline verification passed **220 Python tests, 41 native self-tests and 9 real native UI checks**.

This increment implements a versioned character compilation pipeline, an observation-first v2 domain, a scene-dominant native game interface, seven bundled art assets and explicit save migration. It retains Path A (README/Skill/source/IDE) and Path B (native activation/specialist gameplay) on the same HAL registry and transactional host. It does not replace the specialist engine with a chatbot.

| Verification | Result |
|---|---|
| `bash scripts/verify_witness_local.sh` | **287 Python tests passed**, **52 native self-tests passed**, rebuilt app. |
| Original Research and Returns executions | Research profit **600**, margin **40.0%**; Returns **STANDARD_RETURN**. |
| Negative provider preflight | Manus blocked, expected exit **2**. |
| Actual rebuilt Mac app `--ui-self-test` | **PENDING_FINAL_GUI**. Unique synthetic saves; activation disabled. |
| Unicode output bound | Save **1,999,998 bytes**; export wire **6,914,155 bytes**, below native **8,388,608-byte** limit. |
| Source delivery ZIP | Explicit-source packaging with byte/CRC verification; final details in `WTL03_ARTIFACTS.json`. |
| Paid live OpenAI / real credential | **NOT RUN**, as requested. |

Local logs: `engineering/WTL03_BASELINE_VERIFY.log`, `WTL03_BASELINE_UI.log`, `WTL03_VERIFY.log`, `WTL03_BUILD.log`, `WTL03_UI_VERIFY.log`. Logs are Git-ignored. The portable acceptance record is this receipt, [UAT](WTL03_UAT.md), screenshots and artifact manifest.

## Character integration and authoritative rules

The compiler reads exactly `identity.md`, `memory.md`, `user.md`, `narrator_intro.md` and `case_brief.md` from `integrations/witness_loop/source/`. Named reviewed sections become a bounded `witness-character/v1` artifact. Personality changes have a regression proving the effective model input changes. Build/turn receipts record source hashes and the effective digest:

`5d44d5bd96b2e60b197cc859713225d36382774abe2348d822c7770320af9035`

Stable identity (including younger brother Lin Yu), private NPC knowledge, authorized admissions, uncertain facts, player observations and attributed session memories remain distinct. The complete director story is excluded from model messages and packaged resources. Chinese opening copy comes from the reviewed authoring sources; English opening copy is a maintained translation. A file's existence is not treated as proof of model loading.

Core owns phases, inspections, disclosures, six case actions, evidence links, trust/fear and outcomes. The model may propose intent and supply dialogue. Known family contradictions, unauthorized disclosures, merged phone events, unsupported world claims and obvious language mismatches are validated before transcript/memory commit. Rejected live text receives a fallback with `LIVE_MODEL_REJECTED_FALLBACK` and a reason, while honestly retaining that a provider request was used. Lexical safeguards are not exhaustive semantic validation.

New games show brief → narrator → empty station → deliberate approach → introduction → alternating NPC/player turns. Visible/inspected/authenticated/interpreted/linked are separate flags. No Scene 2 auto-ticket in v2. The recent interrupted outgoing call and the earlier incoming 00:17 brother call have distinct event IDs. Three bounded endings remain reachable. A final review found and fixed a post-verdict discovery inconsistency: old evidence can be reviewed, but new discoveries cannot retroactively change an ending.

## Save and security evidence

Synthetic tests prove v1 migration preserves progress, endings, transcript and memories while leaving `session.json` byte-for-byte intact. New saves are written atomically to `session-v2.json`; legacy clock/ticket acquisitions retain explicit provenance rather than invented inspections. Reset/forget affects active v2 state only and leaves old backups/exports. Unknown/corrupt save formats fail closed.

Regression and negative tests cover archive traversal/symlinks/duplicates/size limits, strict schema and capability effects, secret-shaped inputs, forged observations/state, prompt injection as attributed data, stale/replayed transactions, pre-entrance turns, case confirmation, malformed receipts, save symlinks and migration bypass. Native mocked-provider checks cover strict JSON, refusal/incomplete/error responses, credential echoes, no retries/redirects, bridge injection and arbitrary paths. The private worker does not receive the provider key; the renderer has no key field or network access. The running Core is trusted local code, not an OS security sandbox.

## File-by-file diff summary

Paths are relative to the repository. The five user-authored canonical Markdown files were read, not rewritten.

| File | Change |
|---|---|
| `runtime/trusted_adapters/witness.py` | New v2 state/phase and observation ledger, bilingual routing, admissions, invariants, deterministic endings, explicit migration and post-verdict freeze. |
| `runtime/trusted_adapters/witness_v1.py` | Preserved historical engine for validation, migration and v1 compatibility tests. |
| `runtime/trusted_adapters/character_context.py` | Reviewed five-file compiler, bounded projections, provenance digest, runtime artifact verification. |
| `runtime/trusted_adapters/witness_character.json` | Compiled versioned character artifact consumed at runtime. |
| `runtime/hal_core/interactive.py` | v2 save envelope, non-destructive legacy restore, preflight/confirmation, context receipts, validated staged commit. |
| `runtime/hal_core/registry.py` | Shared hooks for domain migration, public view, context metadata and turn preview. |
| `runtime/tests/test_character_context.py` | Source edit → effective context, source drift independence, director exclusion and unsafe-input tests. |
| `runtime/tests/test_witness_v2.py` | New phases, evidence provenance, two calls, identity/disclosure validation, three endings, shared-Core execution and post-verdict tests. |
| `runtime/tests/test_witness_domain.py` | Explicitly targets preserved v1 behavior. |
| `runtime/tests/test_interactive.py` | v2 transactions, budgets/confirmation, exact-byte migration and hostile save/receipt cases. |
| `runtime/fixtures/witness/harness.json` | Package version 1.1.0; existing strict HAL package contract retained. |
| `runtime/fixtures/witness/README.md` | Updated common developer/consumer domain behavior and review boundaries. |
| `runtime/fixtures/witness/skills/witness/SKILL.md` | Versioned gameplay, provenance and authority instructions. |
| `integrations/witness_loop/ui/index.html` | Real scene, four hotspots, inspection dialogs, captions, history/notebook and native activation controls. |
| `integrations/witness_loop/ui/style.css` | Cinematic composition, sprite layering, responsive layout, focus styling and reduced motion. |
| `integrations/witness_loop/ui/app.js` | HAL-driven state rendering, bilingual UX, sequential input, preview/confirm, safe text DOM and inspection/keyboard behavior. |
| `integrations/witness_loop/native/main.swift` | Strict v2 bridge actions, case preflight and cached semantic classification, isolated UI test bootstrap. |
| `integrations/witness_loop/native/SelfTests.swift` | New bridge confirmation/inspection/language and injection regressions. |
| `integrations/witness_loop/native/UISmoke.swift` | Actual app phase/hotspot/caption/drawer/three-ending checks and screenshots. |
| `integrations/witness_loop/native/check_unicode_bounds.py` | Updated v2 maximal Unicode state/export bound check. |
| `integrations/witness_loop/native/README.md` | Current provider, compilation, save and test boundaries. |
| `integrations/witness_loop/ui/assets/platform_empty.png` | Generated rainy empty railway scene with physical clue props. |
| `integrations/witness_loop/ui/assets/linwu_anxious.png` | Generated transparent anxious anime dispatcher sprite. |
| `integrations/witness_loop/ui/assets/clock_face.svg` | Exact 00:17 scene-clock correction. |
| `integrations/witness_loop/ui/assets/clock_detail.svg` | Exact readable clock inspection view. |
| `integrations/witness_loop/ui/assets/ticket_detail.svg` | Fictional Zhou Xu folded-ticket inspection artwork. |
| `integrations/witness_loop/ui/assets/red_fabric_detail.svg` | Original wet-fabric inspection illustration. |
| `integrations/witness_loop/ui/assets/train_departure_detail.svg` | Original distant-train observation illustration. |
| `scripts/compile_witness_character.py` | Explicit build/check CLI with archival drift reporting. |
| `scripts/build_witness_mac.sh` | Compile context, stage fresh resources, exclude raw story, bundle artwork, emit hashes/version 0.3.0. |
| `scripts/verify_witness_local.sh` | Reject stale character compilation before Core/build checks. |
| `scripts/package_witness_source.py` | v0.3 source delivery, artwork and current docs; excludes saves, credentials, supplied moodboards and caches. |
| `.gitignore` | Excludes supplied reference image directory pending rights decision. |
| `README_START_HERE.md`, `runtime/README.md` | Current increment links while retaining historical baseline. |
| `integrations/witness_loop/README.md` | Current launch, controls, saves, provider limits, authoring and verification. |
| `integrations/witness_loop/SOURCE_PROVENANCE.md` | Corrects historical unchanged-source location without rewriting old evidence. |
| `integrations/witness_loop/ASSET_PROVENANCE.md` | Reference roles, generated/authored distinction, prompts and rights status. |
| `integrations/witness_loop/handoff_v03/WTL029_v0.3_Codex_Integrated_Implementation_Prompt.md`, `REFERENCE_MANIFEST.json` | Local supplied engineering specification and reference manifest. Four ignored reference PNGs were inspected before art creation. |
| `integrations/witness_loop/reference_v01/` | Ten original files recovered unchanged from commit b234d98; original hash inventory remains in source provenance. |
| `engineering/WTL03_DECISIONS.md`, `WTL03_RECEIPT.md`, `WTL03_UAT.md`, `WTL03_ARTIFACTS.json`, `wtl03-screenshots/` | Decisions, verification/diff receipt, reproducible playtest, integrity metadata and actual app captures. |

Existing `engineering/BASELINE_AUDIT.md` and `engineering/SPRINT1_RECEIPT.md` remain the completed earlier HAL contract/security work. This is the later v0.3 implementation receipt.

## Limitations and next steps

- Live OpenAI personality, nuanced bilingual conversation and adversarial paraphrases remain untested. Offline dialogue is explicitly simulated; no claim of “AI verified” from an API key entry alone.
- Reviewed compilation is selective, not arbitrary Markdown hot loading. Authors remain trusted. Canonical identity/knowledge changes need semantic review, and English opening translations require manual synchronization.
- The evidence link and outcomes retain compact MVP rules. They are not an unrestricted detective simulator or a complete reconstruction of the director conspiracy. No model can add evidence or select an ending.
- App is unsigned, not notarized, tied to this checkout/system Python, and tested on this Mac only. No portable distribution, multi-process save editing or encrypted-at-rest memory is promised.
- The native secure sheet, export Save panel, full VoiceOver audit and human aesthetic acceptance still need manual UAT; automated bridge tests do not establish those.
- Generated station/sprite and original SVG details are identified as such. No supplied reference image was published. Distribution rights require a human decision before release.
- Next authorized engineering after review: address concrete playtest feedback; optionally run a separately authorized bounded live-provider UAT; then decide portability/signing and broader semantic validation priorities.

Launch instructions and playable routes are in [Witness Loop README](../integrations/witness_loop/README.md) and [UAT](WTL03_UAT.md). No publication or Human Gate completion was self-approved.
