# Domain package contract: hal-domain/v1

Sprint 1, 2026-10-16. Status: real offline implementation; unsigned packages are inspected as data. The normative validators are `hal_core/schema.py` (package structure), `hal_core/contracts.py` (container/files), the installed typed registry, and `trusted_adapters/value_contracts.py` (specialist values). No dependency download or general JSON Schema interpreter is needed.

## Supported representations and migration

- A directory with `harness.json` at its root; a root-layout ZIP; or a ZIP with exactly one top folder such as `repository-main/harness.json` or `repository-v1.0.0/harness.json`.
- A wrapper must contain every archive entry. Multiple/nested manifests, mixed roots, path aliases, case collisions, symlinks, special files and forbidden files are rejected. Normalization removes one wrapper only; it never extracts or executes files. This is support for common GitHub archive **layout**, not verification of GitHub provenance or arbitrary repositories.
- Existing `hal-demo/v0.2` packages normalize in memory with `LEGACY_SCHEMA_NORMALIZED`. The two demo local ports map to explicit tool contracts; AI features reference the same specialist tool plus a separate model requirement. Migration requires existing `AGENTS.md`, readable source/README/Skills, and exactly one known local demo port per feature. Other legacy forms fail closed. Source bytes, original manifest, source schema and digest remain unchanged.
- `python3 -m hal_core.cli inspect --package fixtures/research --normalized` emits only the v1 manifest. To adopt it, copy a package to a new working directory and save this output as the copy's `harness.json`; do not redirect over the package being inspected. Reinspect the new package. This explicit migration changes its digest because manifest bytes change. Baseline fixtures are intentionally retained at v0.2.
- Plain `inspect` emits original `schema_version`, `normalized_schema_version`, `contract`, normalized file list/digest, wrapper name, warnings and `publisher_verified:false`. Migration does not imply trust or install anything.

## Strict manifest

All objects reject unknown fields. Identifiers match `[a-z][a-z0-9-]{2,63}`; package version is three nonnegative numeric components without leading zeros; contract IDs use `name/vN`. Only `description` is optional at top level. Required asset references must point to real package files and use canonical relative paths.

```json
{
  "schema_version": "hal-domain/v1",
  "id": "research-diagnostics",
  "name": "Research Diagnostics",
  "version": "1.0.0",
  "domain": "research",
  "description": "Deterministic margin analysis from fictional inputs.",
  "entrypoint": "main.py",
  "readme": "README.md",
  "agents": "AGENTS.md",
  "skills": ["skills/research/SKILL.md"],
  "host": {"api": "hal-core/v1"},
  "permissions": {
    "filesystem": "selected_paths_only",
    "external_write": "approval_required"
  },
  "tools": [{
    "id": "calculate-margin",
    "port": "LOCAL_CALCULATE",
    "input_contract": "research-margin-input/v1",
    "output_contract": "research-margin-output/v1",
    "permissions": []
  }],
  "features": [{
    "id": "calculate-margin",
    "tool": "calculate-margin",
    "required_capabilities": [{"port": "LOCAL_CALCULATE", "capabilities": ["calculate"]}],
    "permissions": []
  }, {
    "id": "ai-interpretation",
    "tool": "calculate-margin",
    "required_capabilities": [
      {"port": "LLM_DIRECT", "capabilities": ["tool_calling"]},
      {"port": "LOCAL_CALCULATE", "capabilities": ["calculate"]}
    ],
    "permissions": []
  }]
}
```

Unknown versions/host APIs are rejected; no best-effort version fallback. Tools and features have unique IDs. Every feature references one declared tool, includes that tool's port, and lists each required port at most once. Tools/features are limited to 100 each, Skills to 30, and requirements/capability/permission lists to 15 entries. Duplicate list values are rejected. JSON rejects duplicate keys, nonfinite numbers (including exponent overflow), excessive integer literals and nesting. Secret-shaped keys are rejected recursively; this is not a secret-content scanner.

## Capabilities, permissions and reviewed execution

| Contract | Meaning and current host evidence |
|---|---|
| LOCAL_CALCULATE / calculate | Reviewed Research calculator, available offline. |
| LOCAL_TRIAGE / triage | Reviewed fictional Returns triage, available offline. |
| LLM_DIRECT | Always blocked; provider names are offline classifications, not verified capabilities or credentials. Manus/WorkBuddy names produce managed-agent mismatch in this slot. |
| MANAGED_AGENT, EMBEDDED_CHANNEL, DATA_FEED, TOOL_API | Known types, no installed adapter; blocked. |
| tool_calling, structured_output, streaming | Known requirement names, no live model evidence. A local calculator cannot claim these capabilities. |
| selected_files_read, network, external_write | Known permission requests, all unavailable to tools in this offline host. Required permissions always block; there is no grant API. |

The top-level policy is an exact safe declaration, not OS enforcement or a grant. A tool's ID, port, input/output contract IDs and permission set must match the independently reviewed installed registry record. The package ID is a lookup namespace, not an authenticated publisher identity. Even an unsigned package claiming a known ID can only call the installed pure fixture adapter; its source/Skills are never executed or followed as instructions. Unknown valid tool/contract IDs may be inspected but cannot execute. `feature_status` separates missing ports, missing permissions and available host evidence. A local tool can be available while its AI feature stays blocked.

| Installed value contracts | Validation |
|---|---|
| research-margin-input/v1 | Exact revenue/cost fields; finite numeric values, booleans excluded; revenue > 0, cost >= 0. |
| research-margin-output/v1 | Exact profit/margin_pct/unit/rule; finite numbers and expected method/unit constants. Overflow output is blocked. |
| returns-triage-input/v1 | Exact condition/proof/days; sealed/opened/damaged, yes/no, integer days 0–365 (booleans excluded). |
| returns-triage-output/v1 | Exact classification/rule/fictional-policy marker; known classifications and expected constants. |

These IDs reference host-owned validation functions; imported manifests cannot define code or replace schemas. Run receipts identify the package content digest, normalized contract, selected tool, input/output contracts, validated stages, result or denial, and false live-model/external-write flags. Payloads are not copied into receipts. Handler exceptions are sanitized. Execution remains one synchronous reviewed call with a strict budget of one; there is no general-purpose sandbox or durable agent loop.

## Resource and filesystem limits

1,500 actual entries (including explicit/empty directories), 4,000,000 bytes per file/JSON input, 25,000,000 uncompressed bytes per package, 30,000,000 ZIP container bytes, per-member compression ratio <= 200. ZIP_STORED and ZIP_DEFLATED only; encrypted, damaged or unsupported archives are rejected. Paths have at most 32 components and 1,024 UTF-8 bytes; noncanonical Unicode, controls, reserved Windows names and nonportable separators are rejected.

Directory traversal uses descriptor-relative reads and no-follow opens; ZIP opens use no-follow descriptors and metadata checks. This implementation requires POSIX-style no-follow capabilities; unsupported platforms fail closed, and Windows/native support remains unverified. Files are read with limits and checked for detected changes, but no atomic snapshot or hostile-filesystem isolation is claimed. Every container error becomes a static diagnostic rather than echoing archive filenames or OS exception text.

## Shared architecture and remaining work

Path A uses the same validated README, AGENTS, Skills and source package; the CLI never auto-runs the entrypoint. Path B can consume the normalized feature/tool contract and readiness results through a future trusted bridge. The existing Ready HTML preserves provider education and specialist controls but remains separate, with simulated model activation. This sprint adds no browser service, credential storage, source export UI or generic chatbot.

Publisher signatures, license/provenance verification, signed installation, authenticated UI/native IPC, real repository adapters, live providers and user-grant workflows remain future work. File digest equality is content equivalence only, not a signature test. F02/F06/F07/F08/F10/F13 are advanced within this bounded contract; F14–F16 are not delivered.
