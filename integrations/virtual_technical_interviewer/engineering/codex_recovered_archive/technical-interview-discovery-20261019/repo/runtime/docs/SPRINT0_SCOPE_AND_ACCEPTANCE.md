# HAL Sprint 0 — Authorized Scope and Acceptance

Approval: Human Gate **DOING** received 2026-10-14. The approval permits bounded implementation, local offline testing and the creation of source artifacts. It expressly prohibits public GitHub publishing and real user API keys; no model bills or external writes are permitted by this implementation.

## Delivered vs original v2 contract

| ID | PRD v2 requirement | Sprint 0 truth | Evidence | Remaining |
|---|---|---|---|---|
| F02 | Domain manifest | PARTIAL REAL | strict `hal-demo/v0.2` package validator, source ZIP/dir inspector, SHA-256 digest | schema migration, signed manifest and compatibility mapping |
| F06 | Provider preflight | OFFLINE CONTRACT ONLY | `MANAGED_AGENT_PORT_MISMATCH`, direct LLM requires live verification | versioned provider capability test + consented key broker |
| F07 | Domain swap | REAL CLI-SCOPED | same core runs different packaged demo IDs with same interface | frontend runtime link / non-demo repo packages |
| F08 | Domain core | REAL CURATED | two deterministic tool adapters, identical golden outputs as MVM | specialist integration tests with external repos |
| F10 | Feature readiness matrix | PARTIAL REAL | declared port + trusted adapter registry + blocked missing model port | actual tool/model readiness and cost observation |
| F13 | Negative/recovery path | PARTIAL REAL | invalid input blocked; no stale results, no untrusted execution | long jobs, resume, state durability and cancellation |
| F14 | Native secret broker | NOT IMPLEMENTED | no secret accepted | native OS keychain in trusted process with integration tests |
| F15 | Real bounded Agent runtime | NOT IMPLEMENTED | one curated synchronous step; no model calls | real model adapter, bounded loop, tools, usage, checkpoint, approvals |
| F16 | 2 external repo integrations | NOT IMPLEMENTED | two synthetic independent domain fixtures only | locate/authorize genuine source repos, measure unchanged HAL core and effort |
| F01,F03–F05,F09,F11,F12 | Consumer UX/exports | BASELINE READY MVM | references to v2 deliverable only | wire shell to real trusted local service and validate |

**No production/commercial readiness claim.**

## Gate criteria before next Sprint

1. Confirm operating system (macOS/Windows/Linux), distribution target and local native runtime choice.
2. Confirm two legal, real and trusted source repos or packaged Type B harnesses; inspect licenses and dependencies first.
3. Confirm initial provider and model version for live model capability work. **Permission to engineer adapter code is separate from permission to use a real key or spend credits**.
4. Approve local network and filesystem permissions; define prohibited effects and approval UX.
5. Define real domain outcome and falsifier for the first specialist run; retain plain GitHub+IDE comparison baseline.
6. Review proposed PRD-Compiler v2.1 patch independently; this DOING decision did not authorize installing/modifying the Skill by itself.

## Human validation

- Run example CLI commands from README; compare receipts to expected.
- Try a ZIP with `../` or `.env` and verify rejection.
- Ask for `ai-interpretation` with Manus or OpenAI; verify BLOCKED, not silently successful.
- Request unauthorized task or fake provider tool; verify BLOCKED.

Expected next stage after review: continue DOING only for newly scoped engineering, or move to Review when actual scoped milestones are met. Public release requires a separate user decision.
