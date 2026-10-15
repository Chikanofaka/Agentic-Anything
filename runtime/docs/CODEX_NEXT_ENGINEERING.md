# Codex Engineering Brief — HAL v2 / Sprint 1 Candidate

## Mandate
Continue the v2 Domain Swap Lab HAL architecture from this **verified, offline Sprint 0 Core** and `HAL_PRD_v2_0` without rebuilding the need/ideation story or disguising simulation as production. This brief is *a plan*, not evidence a Codex agent has been dispatched.

## Read order
1. `README.md`, `docs/SPRINT0_SCOPE_AND_ACCEPTANCE.md` and `docs/SECURITY_AND_LIMITATIONS.md`
2. `hal_core/contracts.py`, `hal_core/ports.py`, `hal_core/registry.py`, `hal_core/engine.py`, `trusted_adapters/`, `tests/`
3. Baseline HAL v2: `prd/HAL_PRD_v2_0.md`, `prd/TRACEABILITY.csv`, `prd/UAT_MATRIX.md`, `prd/ARCHITECTURE_OPTIONS.md`, `skill-feedback/PILOT_RECURSION.md`, `ready-mvm/index.html`

## First engineering story: harden package activation
- Adopt versioned normalized package schema (not the hardcoded demo manifest) with explicit `tools`, permissions, inputs, outputs, host compatibility and version migrations.
- Accept common GitHub ZIP top-folder layout by safe normalization. Reject ambiguous multi-root ZIPs and symlinks.
- Verify provenance/signatures/license expectations and package publisher trust. Do not execute arbitrary repository code because the package parses.
- Support domain adapters through reviewed, separately registered tool contracts; no manifest-to-import or manifest-to-shell injection.
- Keep all negative tests, add malformed JSON, zip bombs, path resolution fuzz tests and integrity-signature tests.

## Next story: UI-to-runtime trust bridge
- Bind HAL Shell feature declarations to an authenticated localhost/native IPC interface; avoid unauthenticated externally routable port.
- Retain both A Developer README/ZIP and B Intelligent Key Academy/Activation.
- Build a trusted native API-key broker for the chosen OS using OS secure storage, with no secrets crossing to JS renderer.
- Until explicit user authorization for keys/spend, use a dedicated dummy adapter with zero network and clear status `SIMULATED`.
- Include cancel/retry, user-permission prompts, failure and recovery states. No decorative chat-only shortcut.

## Next story: genuine specialty Agent loop
- Only after separate permission to connect real credentials, verify one chosen model's actual tool calling and structured result support using a dedicated restricted key with budgets.
- Integrate a real domain task with separately authorized data/tool access. Persist source and permission provenance in redacted run receipt.
- Compare two independent authorized GitHub repositories with a GitHub+IDE baseline. Quantify hours to adapt without rewriting `hal_core`.

## Hard non-goals
No public GitHub, no real API keys without new permission, no paid provisioning, no production deployment, no arbitrary repo code or CLI commands, no editing upstream repositories until chosen/authorized, no secret exposure in PRD or logs.

## Review gates
All regression + red-team negative tests pass; no confusion between declared and operational ports; explicit file and model/data permissions; truthful run receipts; traceable F02/F06/F07/F08/F10/F13 improvements; human review before any outside operations.
