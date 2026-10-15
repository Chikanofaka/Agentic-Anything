# Security and Execution Boundary — Sprint 0

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
`tests/test_hal.py` tests rejection of symlinks, ZIP traversal, .env, manifest secrets, missing referenced files, unsafe requested permissions, unsupported model port, invalid domain input, secret field, unknown/untrusted domain and model execution before adapter installation.
