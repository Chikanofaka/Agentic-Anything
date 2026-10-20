# TIA offline slice — implementation handoff

Branch: `feat/tia-s02-traceability`. Base: `21512016ba46fa81dec9ece659e6b25370a93333`. Local commit only; no push or live provider.

Implemented independent Interviewer/Trainer contracts, a provider-neutral offline portal, a host-owned session controller, and an executable deterministic CLI. Existing S02 files remain byte-identical (221 tracked TIA artifacts checked).

## Run

```sh
python3 -B integrations/virtual_technical_interviewer/offline_demo.py
python3 -B integrations/virtual_technical_interviewer/offline_demo.py --json
python3 -B integrations/virtual_technical_interviewer/run_tests.py
```

## Actual results

- 40 TIA tests passed on the working branch: [test output](receipts/tia_tests.log).
- HAL baseline: 287 tests + CLI assertions passed before the additive change; shared HAL files were not modified: [baseline output](receipts/hal_baseline.log).
- Demo reached COMPLETE with 18 events; reviewed receipt unchanged after Trainer: [CLI output](receipts/demo.log), [JSON receipt](receipts/demo.json).
- `--provider openai` exited 2 with LIVE_PROVIDER_DISABLED: [denial output](receipts/live_provider_blocked.log).
- Full machine receipt: [verification.json](receipts/verification.json). Observed interpreter: Python 3.9.6.
- Initial repository-root unittest discovery exposed an import-path issue; `run_tests.py` fixes that entrypoint. The [initial failure log](receipts/tia_tests_initial_import_failure.log) is retained separately from the final passing run.

## Source and authority

`tia_runtime/controller.py` follows HAL's reviewed-host boundary: only the host changes phase, event history or role handoff. `provider.py` follows the typed/bounded adapter pattern in `integrations/witness_loop/native/OpenAI.swift`, with no HTTP, credentials or SDK. `contracts.py` validates data-only role manifests. This slice does not modify or claim registration in the shared HAL CLI/Witness interactive registry.

Canonical requirements: v3 FR-03/04/05/08/12/27 and COM-FR-001/007/009/010/012, narrowed by the user's explicit implementation request. These are partial mechanism links, not full FR/M0 acceptance. Earlier S02 matrices remain unchanged and retain their original NOT_RUN statuses.

## Limits

Candidate dialogue, model responses, fixture clock and handoff review are synthetic. Session transitions, timeout/error validation, event capture and receipt isolation execute locally. Technical and Communication are separate NOT_SCORED ledgers. No SQL evaluator or full scoring system is implemented. The Trainer receives only the closed reviewed packet; its drill is simulated and does not demonstrate learning transfer. State is in memory; restart persistence, full HAL registry integration, live providers and production grading remain outside this slice.
