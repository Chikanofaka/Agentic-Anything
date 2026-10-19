# HAL-P2D-001 — DOING Sprint 1 (offline)

**2026-10-17 v0.3 increment:** [Witness Loop launch guide](../integrations/witness_loop/README.md) and [current receipt](../engineering/WTL03_RECEIPT.md) describe the cinematic native app, compiled character context, observation ledger and non-destructive v1→v2 migration. Both entry paths still use this HAL Core. The historical CLI scope below does not describe the newer native host's implemented, mock-tested OpenAI adapter.

**2026-10-16 application increment:** [Witness Loop](../integrations/witness_loop/README.md) adds a third reviewed domain, a shared transactional interactive host, persisted state and a native Mac UI/broker. The OpenAI adapter is implemented with mocked responses; real credentials/inference remain untested. The Sprint 1 description below is retained for the offline CLI, whose model preflight still fails closed. See the [current integration receipt](../engineering/WITNESS_INTEGRATION_RECEIPT.md) for new evidence and limitations.

**Approved Human Gate:** DOING, 2026-10-14. Scope remains restricted: no public GitHub, no real API keys, no billable inference and no external data access.

This is a **real deterministic prototype of the HAL Core**, not an AI agent or production desktop installer. It is grounded in the `HAL_PRD_v2_0`, `Domain Swap Lab`, and PRD-Compiler recursive feedback. It proves a small common execution contract for two separately packaged specialist demo domains.

Sprint 1 adds strict `hal-domain/v1` validation, explicit legacy normalization, safe common GitHub ZIP wrapper handling, typed installed tool/value contracts and effect denials. See [package contract](docs/DOMAIN_PACKAGE_V1.md), [baseline audit](../engineering/BASELINE_AUDIT.md), and [Sprint 1 receipt](../engineering/SPRINT1_RECEIPT.md). Historical Sprint 0 receipts remain unchanged.

## What works (REAL)

- Inspect a local directory, root ZIP, or one unambiguous GitHub top-folder ZIP. No extraction or imported code execution.
- Validate explicit file paths, manifest schema, required Skills, permission declarations, size limits, secrets filename patterns, and reject symlinks/unsafe ZIP paths.
- Normalize demo manifests to `hal-domain/v1` without rewriting them. Match tool IDs, ports, value contracts and permission requests against a **trusted adapter registry**. Required unavailable permissions or model capabilities block activation.
- Dispatch two curated deterministic domain methods via *one* HAL Core (no modifications to core between the domains): Research Diagnostics (revenue/cost/profit/margin) and Returns Operations (fictional returns triage).
- Return machine-readable run receipts with selected feature, package SHA-256 content digest, internal state events, result and explicit `live_model_used:false` / `external_writes:false`.
- Refuse unknown/untrusted package code execution, model features without a real verified adapter, secret-shaped input fields and invalid specialist inputs or nonfinite outputs.

## Quickstart — standard-library Python only

Python 3.10+ is the recommended baseline; the actual available interpreter tested in this workspace is 3.9.6. This is observed compatibility, not a verified OS/interpreter support matrix. Safe filesystem import currently needs POSIX no-follow descriptor support; unsupported platforms fail closed. No dependencies were installed.

Extract ZIP, open terminal **from this folder**:

```bash
python3 -m hal_core.cli inspect --package fixtures/research
python3 -m hal_core.cli inspect --package fixtures/returns
python3 -m hal_core.cli inspect --package fixtures/research --normalized
python3 -m hal_core.cli run --package fixtures/research --feature calculate-margin --payload '{"revenue":1500,"cost":900}'
python3 -m hal_core.cli run --package fixtures/returns --feature triage-return --payload '{"condition":"sealed","proof":"yes","days":5}'
python3 -m hal_core.cli preflight --package fixtures/research --feature ai-interpretation --provider manus
python3 -m unittest discover -s tests -v
```

Expected research result: `profit=600`, `margin_pct=40.0`. Expected returns classification: `STANDARD_RETURN`. The Manus preflight is **blocked** and exits code 2; that is expected.

You can inspect original ZIPs from Ready v2 (place them in this folder first, or pass their existing local absolute paths):

```bash
python3 -m hal_core.cli inspect --package path/to/research-harness.zip
```

## Boundaries and explicit nonclaims

- **No true LLM connection or agent loop**. A provider preflight is *offline contract logic*, **not evidence of a valid API key or live model capability**.
- **No key storage UI and no OS keychain bridge**. The CLI rejects secret-like payload fields. Do not pass real keys to it.
- **Not a code sandbox**. It intentionally does not import or execute source code from user-provided packages. ZIP inspection alone is not a malware scanner or license audit.
- **No dynamic discovery of arbitrary GitHub tools**. Only hardcoded trusted adapter bindings exist. This proves separation between HAL Core and domains, not arbitrary plug-and-play.
- **No browser/desktop packaging** in Sprint 0. The Ready HTML MVM remains a standalone UX reference, not yet wired to this runtime.
- **No third-party repo integration**. Both domains are synthetic fixtures from HAL v2, not validated outside repositories.

## Source and next handoff

- `docs/SPRINT0_SCOPE_AND_ACCEPTANCE.md` — requirement mapping, completion status, UAT gates
- `docs/DOMAIN_PACKAGE_V1.md` — current strict package contract, migration, capability and permission rules
- `docs/SECURITY_AND_LIMITATIONS.md` — threat model and real safety boundaries
- `docs/CODEX_NEXT_ENGINEERING.md` — scoped Codex instructions and blockers
- `docs/DECISION_AND_SOURCE_LEDGER.md` — baselines and architectural decisions
- `receipts/TEST_RESULTS.md` — test counts and reproduction steps

**Trello:** [Doing v2](https://trello.com/c/4p7UB58X) · [Idea PRD v2](https://trello.com/c/9CXhk2o0). Do not treat DOING as publication consent.
