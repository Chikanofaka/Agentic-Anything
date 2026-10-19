# Codex Implementation Handoff — HAL v2 PRD Pilot

**Read first**: `prd/NEED_NORMALIZED.md`, `prd/HAL_PRD_v2_0.md`, `prd/TRACEABILITY.csv`, `prd/UAT_MATRIX.md`, `prd/ASSUMPTIONS_AND_OPEN_QUESTIONS.md`, `prd/ARCHITECTURE_OPTIONS.md`, `prd/MVM_SPEC.md`, then `ready-mvm/index.html`, `receipts/TEST_RESULTS.md`, and `skill-feedback/PILOT_RECURSION.md`.

## Before writing runtime code (human DOING required)
1. Verify scope, first OS, legal license, production domains, user data privacy, provider/region. Do not guess values or use historical enterprise budgets.
2. Inspect two real and legally usable specialist repositories, map their entrypoints and domain-specific validation; compare with plain GitHub/IDE baseline.
3. Adopt or modify the v0.2 manifest contract and generate strict schema/path/license validation tests. The MVM's embedded `domains` JavaScript object is not an installed plugin loader.
4. Implement the provider **model adapter** separately from managed-agent, channel and data/tool adapters. Determine actual tool-calling and structured-output capabilities per chosen model/version.
5. Keep raw API keys in trusted OS/native code and system credential store; never place in browser renderer, source ZIP, localStorage, logs or prompt history. Ask scoped authorization for file/network/external effects.
6. Implement event-sourced bounded agent loop with max steps, budget ceiling, cancel, timeout/retry, redacted receipt and fail-closed human approval on side effects.
7. Deliver a real validated specialist artifact (not a generic text-only chatbot) with sources and negative security cases.
8. Integrate a second *different* genuine domain repo without changing the HAL core and measure engineering-hours/quality vs bespoke.

## Explicitly not requested / forbidden shortcuts
- Do NOT infer package safety from a SKILL.md or file name.
- Do NOT treat mock preflight as live API connectivity.
- Do NOT substitute a vanilla chatbot for feature/tool binding.
- Do NOT claim all providers share key semantics or grant access to paid enterprise datasets.
- Do NOT publish repositories or installers without separate written Human approval.

## Deliverables per PRD acceptance
Architecture implementation decision + rationale; package schema and validators; threat model; one real provider adapter; source/permission fixtures; trace; actual domain report; test log with fail paths; clean-machine installer evidence; effort estimate with currencies/units and open dependencies; 2nd real domain integration receipt.

## Current Gate
**READY_FOR_HUMAN_UAT_WITH_DEBT / PENDING**. Do not start production by interpreting this document alone as permission.
