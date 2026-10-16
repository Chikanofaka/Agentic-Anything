# Security and Execution Boundary — Sprint 0 baseline and Sprint 1 update

## Witness application increment — 2026-10-16

The historical CLI boundary below remains unchanged. A separate native Mac host now implements an in-memory credential sheet, fixed-endpoint OpenAI adapter and restricted bundled-page bridge to the same HAL runtime via private stdio. It has no localhost listener. Only mock provider tests were run: no live credentials or paid requests. See [native boundaries](../../integrations/witness_loop/native/README.md) and the [integration receipt](../../engineering/WITNESS_INTEGRATION_RECEIPT.md) for current controls. The interactive host persists bounded plaintext user dialogue/state in a fixed local directory; its receipts' `external_writes:false` means no third-party write, not no local save. The trusted parent supplies language provenance; these receipts are not cryptographic attestations. Single-process ownership of a session is assumed. Neither host nor worker is an OS sandbox, and narrative consistency is not guaranteed by prompt instructions.

## Sprint 1 update — 2026-10-16

The current implementation adds strict `hal-domain/v1` with explicit legacy normalization, canonical paths and one-wrapper ZIP normalization, bounded no-follow file reads, archive metadata/CRC error handling, recursive secret-shaped field checks, typed host tool contracts and finite input/output validation. Required effects remain unavailable and block execution. See `DOMAIN_PACKAGE_V1.md` for exact limits and `../../engineering/SPRINT1_RECEIPT.md` for executed evidence. These controls strengthen the following baseline; they do not authenticate publishers, verify licenses, scan arbitrary secret contents, isolate processes or implement a native credential broker. POSIX no-follow support is required and the observed interpreter is Python 3.9.6; other platforms are not certified. Concurrent changes are checked where possible, but the inspector is not an atomic filesystem snapshot.

The package ID selects a reviewed pure host adapter; matching it does not prove source trust. Registered value schemas live with trusted adapters. No source module path or shell target comes from a manifest. CLI errors and tool exceptions use static diagnostics, and payload JSON rejects duplicate keys/nonfinite values. New tests cover import attacks, schema/compatibility, capability/permission escalation, malformed CLI inputs and specialist numeric/output failure paths.

## Assets and adversaries
Assets: user files, API keys, private business data, filesystem and machine resources, external accounts. Threats: ZIP path traversal, malicious untrusted package code, symlink escape, coercive feature permissions, hidden secret files, endpoint mismatch, prompt injection in README/Skill, false readiness signals.

## Actual controls
- Imported ZIPs and directories are read as data, with size/count/path restrictions and simple secret-filename detection. **No source is imported or evaluated from those packages.**
- The runtime uses an installed `TRUSTED` adapter map; manifest declarations are not authority to execute new tools.
- `external_write` must be `approval_required`; `filesystem` must be `selected_paths_only`. **These are validated declarations, not a proven OS-enforced sandbox.**
- Direct model and managed-agent families are distinct. Offline preflight never calls a provider or claims key validity.
- CLI structured receipts contain no input payload and reject common secret-bearing field names; there is no persisted user input database.
- No network clients, cloud connections, repo publication, key storage, payment or external-write functions are implemented.

## Limitations / risks remaining
- File content itself is not fully scanned for secrets/malware; `inspection passed` is **not** a trust certificate.
- The parsed manifest is not signed, and no publisher provenance verification exists.
- Python process runs with current user's machine privileges; trust is currently limited to the shipped HAL source modules. It is **not** a hardened general-purpose sandbox.
- The one-step tool budget is narrow, and runtime's synchronous allowed tools currently have no isolation/kill/timeout process boundary. Do not use it to run untrusted or long-running tools.
- Future renderer/localhost interfaces will need an authenticated native-to-web bridge, CSRF/session protections and explicit network/file policies.
- Future native secure storage must not export raw API keys to browser JavaScript and must have rotation, revocation and budget controls.
- No credential was collected or used; no provider was called; no third-party database was accessed; no GitHub repository was modified.

## Negative tests
`tests/test_hal.py` preserves baseline cases. `test_package_security.py`, `test_schema.py`, `test_capabilities.py` and `test_cli.py` add Sprint 1 negative and regression coverage; use `bash ../scripts/verify_local.sh` from runtime for the full suite and actual CLI output/denial assertions.
