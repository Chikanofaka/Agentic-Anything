# HAL-P2D-001 Sprint 1 implementation receipt

Date: **2026-10-16**, Asia/Shanghai. Human Gate remains **DOING**. Scope delivered: bounded local package activation hardening, not product Completion or release approval.

## Outcome

Implemented strict `hal-domain/v1`, explicit in-memory legacy migration, safe common GitHub ZIP wrapper normalization, reviewed typed tool/capability/value contracts, unavailable-permission denials and structured errors. Both specialist domain tasks still run through the same Core. Imported source is never executed. The consumer MVM is preserved as a separate UX/simulation reference; no generic chatbot or native service was created.

Baseline audit was written before implementation: [BASELINE_AUDIT.md](BASELINE_AUDIT.md). The approved PRD, baseline examples/ZIPs, MVM, original runtime fixtures, Sprint 0 receipts, Human Gate and candidate Skill remain unchanged.

## Executed verification

Environment: **Python 3.9.6**, local macOS workspace. The original documentation expected 3.10+; only the actually available interpreter is claimed as tested. No dependency installation or network access occurred. POSIX no-follow descriptor support was available. Cross-platform/3.10+ verification remains open.

| Command | Result |
|---|---|
| Before edits: `bash scripts/verify_local.sh` | Exit 0, 31/31 baseline tests; both domain outputs correct. Original script only printed expected Manus denial. |
| Before edits, from runtime: `python3 -m hal_core.cli preflight --package fixtures/research --feature ai-interpretation --provider manus` | Exit 2, BLOCKED/MANAGED_AGENT_PORT_MISMATCH. Also exposed the false missing-local-tool diagnostic, now fixed. |
| After edits: `bash scripts/verify_local.sh > engineering/verify_local.log 2>&1` | **Exit 0; 136/136 tests passed, no failures/errors/skips**, 1.280 seconds for unittest in this run. Actual CLI inspection, two golden results and Manus denial are asserted. |
| `git diff --check` | Exit 0; no whitespace errors. |

Full final output: [verify_local.log](verify_local.log). Earlier targeted runs were diagnostic/integration checks; the final count comes from the complete verifier, not a sum of repeated runs.

| Suite | Tests | Evidence covered |
|---|---:|---|
| Existing `test_hal.py` | 31 | Original domain regression and security boundaries preserved. |
| `test_package_security.py` | 43 | Root/wrapper ZIP equivalence, ambiguity, paths/case collisions, symlinks/FIFOs, no extraction, size/count/ratio limits, corrupted/encrypted/unsupported ZIPs, JSON/Unicode, secret-shaped declarations, symlink replacement during open and depth limits. |
| `test_schema.py` | 29 | Strict v1 and nested types/fields, versions/host, asset references, duplicate declarations, permissions, legacy normalization and unchanged source/digest. |
| `test_capabilities.py` | 24 | Both v1 domain executions, independent AI/local resolution, full tool contract matching, effect/capability denials, typed inputs/outputs, huge numbers, nonfinite results and sanitized tool failures. |
| `test_cli.py` | 9 | Real subprocess CLI JSON/exit codes, normalized manifest output without mutation, both specialists, malformed/duplicate/nonfinite/oversized payloads, broken ZIPs and Manus denial. |
| Total | **136** | Includes table-driven adverse variants within individual tests. |

## Demonstrated behavior

- Research 1500 revenue / 900 cost -> **profit 600.0, margin_pct 40.0**. Receipt records `research-margin-input/v1`, `research-margin-output/v1`, INPUT_VALIDATED and OUTPUT_VALIDATED.
- Returns sealed / proof yes / 5 days -> **STANDARD_RETURN**, `fictional-returns-v1`, `not_a_real_business_policy:true`. Separate inputs, outputs and specialist validation remain intact.
- Both receipts: SUCCESS, DETERMINISTIC_OFFLINE, `contract_schema:hal-domain/v1`, `permissions:[]`, `live_model_used:false`, `external_writes:false`.
- Manus direct-model preflight: **exit 2 / BLOCKED**; missing ports is exactly `[MANAGED_AGENT_PORT_MISMATCH]`, while the local calculator is AVAILABLE_CURATED_LOCAL. Recognized direct providers also remain blocked as unverified.
- Required selected-file, network or external-write permissions block before a handler call. Manifest declarations cannot grant effects or substitute a host value contract.
- Both root ZIP and single GitHub wrapper ZIP preserve normalized content/digest and domain identity. Malicious/unreviewed source remains inert; mismatched or unknown tools cannot dispatch.
- Numeric regressions: huge Python integer input returns a blocked receipt instead of OverflowError; finite inputs whose calculation overflows cannot return a successful infinite result. Invalid runs expose no result or previous result.
- `inspect --normalized` provides a reviewable v1 manifest without changing a source package; unknown versions and unsupported legacy shapes fail closed.

Original fixture digests remain:

| Domain | SHA-256 |
|---|---|
| Research | `f1e7edf1efa0b3bf87c1acd69edd453aa95b6a21648c415d64eadd02a8078e6f` |
| Returns | `fb11240fdbb983a29456b5f80eaefe7791fcb7ed5ca1e3a4b4c30d26410ec0ac` |

These are integrity identifiers, **not authenticated publisher signatures**.

## Changed files

| Files | Purpose |
|---|---|
| `runtime/hal_core/schema.py` (new) | Versioned strict manifest validator and explicit bounded demo migration. |
| `runtime/hal_core/contracts.py` | Safe bounded directory/ZIP reads, one-wrapper normalization, strict JSON, canonical paths, collision and malformed-archive handling; expose normalized contract and source metadata. |
| `runtime/hal_core/registry.py` | Typed ports and immutable installed callable/tool records. |
| `runtime/hal_core/ports.py` | Resolve feature requirements against the declared tool and host evidence; separate permission denials. |
| `runtime/hal_core/engine.py` | Enforce reviewed binding, budget, typed input/output checks and sanitized failures; enrich receipts. |
| `runtime/trusted_adapters/value_contracts.py` (new) | Host-owned specialist input/output validators, kept outside the generic Core. |
| `runtime/hal_core/cli.py`, `runtime/hal_core/__init__.py` | Normalized manifest command option, strict CLI JSON/finite receipts and current runtime label. |
| `runtime/tests/test_package_security.py`, `test_schema.py`, `test_capabilities.py`, `test_cli.py` (new, all under runtime/tests) | 105 additional regression/security tests. Existing 31 tests untouched. |
| `scripts/verify_local.sh` | Report interpreter; actually execute and assert CLI golden outputs and negative preflight. |
| `runtime/docs/DOMAIN_PACKAGE_V1.md` (new) | Contract, example, migration, exact resource limits, capabilities/permissions and extension boundaries. |
| `runtime/docs/SECURITY_AND_LIMITATIONS.md`, `runtime/README.md`, `README_START_HERE.md` | Current implementation and interpreter evidence; preserve distinction from historical Sprint 0. |
| `engineering/BASELINE_AUDIT.md`, `engineering/SPRINT1_RECEIPT.md`, `engineering/verify_local.log` (new) | Baseline evidence, final implementation receipt and raw verification output. |

## Pathway and requirement trace

| Requirement / UAT | Sprint 1 evidence and boundary |
|---|---|
| F02 / T02 | REAL strict versioned manifests, explicit host API, wrapper import and nonmutating legacy migration. No signature/license verification. |
| F03–F04 / T03–T04 | REAL validation of README/AGENTS/Skills/source references and rejection of unsafe packages. Existing Path A source ZIP/IDE onboarding preserved; no new exporter or arbitrary-source execution. |
| F06 / T06 | REAL offline typed provider-port denial; no live provider capability verification. |
| F07–F08 / T07–T08 | REAL shared Core with Research and Returns; both legacy and v1 contracts tested. Synthetic fixtures only. |
| F10 / T10 | REAL feature-to-tool/value/capability mapping and separate missing permission diagnostics. No grant workflow yet. |
| F13 / T13 | REAL structured errors, input/output rejection and no failed-run result. Cancellation/recovery of durable jobs remains absent. |
| F01/F05/F09/F11/F12 | Existing Path B meta-onboarding, provider education, specialist controls and simulation labels remain in the MVM. Source reviewed, no new browser UAT or UI-to-Core integration claimed. |
| F14–F16 | NOT IMPLEMENTED: native vault, real model/tool agent loop, two genuine external repo integrations and measured adaptation effort. |

## Limitations and next implementation steps

REAL means local deterministic code and tests above. SIMULATED means MVM provider activation/AI explanations. ASSUMED means proposed native architecture, provider compatibility and consumer value. OUT_OF_SCOPE means live credentials/inference, paid calls, network services, external data/writes, publication/deployment and Skill promotion.

1. Review this narrow contract and select the first supported OS/native transport. Next local slice: an authenticated offline UI-to-Core bridge that consumes the same feature contracts and serves specialist forms/results while retaining developer docs and consumer education. Define session/CSRF/origin protections before exposing a listener; no listener was started here.
2. Define publisher trust, license expectations and signature verification. Digests plus schema validation do not establish provenance. Filename/field checks are not a complete secret/malware scanner. Some ordinary repositories will intentionally be rejected by conservative layout, file-type or resource rules.
3. Choose and authorize genuine domain repositories and their licenses/data. Add reviewed tools and specialist contracts outside the generic engine; retain their native outcomes and compare integration effort without rewriting Core. Current legacy migration is expressly limited to the two demo port families.
4. Test the chosen OS/Python versions and clean-machine path. Current importer relies on POSIX no-follow capabilities; other environments fail closed and are unverified. Reads check detectable changes but do not form an atomic filesystem snapshot. The synchronous Python process is not a sandbox or timeout/cancellation boundary.
5. Design mocked native broker, grants, bounded model loop and durable failure/cancel states. Real keys, provider calls/spend, external effects and publication still require separate explicit authorization. No permission is needed to continue separately scoped safe local engineering already authorized by DOING.

No network/provider/keychain integration, source publication, remote repository operation, external account write or Skill promotion occurred. Stage remains **DOING**.
