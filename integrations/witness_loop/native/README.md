# Native HAL host — local macOS prototype

Build from the HAL repository root:

```bash
bash scripts/build_witness_mac.sh
```

This uses the existing Apple Swift compiler and system Python; it installs nothing. The unsigned local app is `../dist/Witness Loop.app`. The build embeds reviewed `hal_core`, `trusted_adapters`, `fixtures`, and the specialist game UI. It records this checkout's absolute path for the session data directory; it is a development build, not a portable/notarized release. Rebuild after changing runtime or UI sources.

## Boundaries

- AppKit owns the native secure credential sheet and consent. The provider key is session-only, cleared on Disconnect or Quit, never passed to JavaScript, Python, a file, or an app log. This is ordinary process memory, not guaranteed zeroizable memory or a hardened OS sandbox. A pasted key remains in the user's system clipboard until the user changes it.
- The fixed provider endpoint is `https://api.openai.com/v1/responses`. The default model is `gpt-4.1-mini`; model names are configurable and access is not assumed. Activating only stores the key locally and reports `ACTIVATED_UNVERIFIED`. A successful schema-valid classifier response changes that to `LIVE_VERIFIED`. This is session access evidence, not a production/provider compatibility certification.
- Each model turn uses up to two requests (topic classification and character reply), with strict JSON schemas, `store:false`, 200/600 output tokens and 30-second request/resource timeouts. A session permits at most 20 requests. Explicit reactivation starts another budget after the native consent sheet. These are request/output limits, not a dollar ceiling; provider retention and charges still apply. There are no app retries or redirects. `URLSession` uses ephemeral storage with cookies, caches and shared credentials disabled.
- Native response parsing rejects refusals, incomplete/HTTP failure responses, malformed/duplicate-key/nonfinite JSON, excessive nesting, oversized bodies, wrong output shape and an echoed session key. Provider error bodies are never shown. Native schema extraction takes topic labels from the reviewed Core's domain contract.
- The page has no credential field, network access, endpoint selector, filesystem API, model-result submission, or process spawning API. The bridge only accepts the bundled main frame, bounded unique request IDs and exact allowlisted actions/parameters. All page navigation/popups outside that file are denied. Text responses are JSON serialized, never assembled as script fragments from user data.
- The native host alone chooses `SIMULATED` versus `LIVE_MODEL`. The Core stages a draft, then atomically commits a validated reply. Provider failure cancels the draft; it does not silently manufacture a live response. Cancellation invalidates callbacks and cleans up drafts. Once the final commit request has been sent to Core, cancellation reports that the save has already begun; it cannot undo that committed operation. Disconnect clears the credential even at this boundary.
- The child Python process has a minimal environment and private standard input/output pipes. It does not receive provider credentials or permission to run arbitrary package code. It remains trusted code running as the current user, not an OS sandbox. Core responses are capped at 8 MiB to accommodate bounded Unicode state/export expansion; incoming Core messages are capped at 32 KiB.
- Export uses an explicit native Save panel; deletion confirmation uses a native confirmation sheet. Export includes only Core's state, readable memory projection and receipt. Existing exports are not erased by forgetting in-app memory.

## Verification commands

The build runs the no-GUI native suite automatically:

```bash
'integrations/witness_loop/dist/Witness Loop.app/Contents/MacOS/WitnessLoop' --self-test
```

It uses synthetic values and `URLProtocol` mocks; no actual provider connections or real credentials are involved. The checks cover request construction, bounded parsing, duplicate keys, refusal/incomplete/errors, key echoes, no retries/redirects and renderer command restrictions.

The optional local GUI integration check is:

```bash
'integrations/witness_loop/dist/Witness Loop.app/Contents/MacOS/WitnessLoop' --ui-self-test
```

This opens the actual WKWebView, tests JavaScript → native → private Core → renderer for both developer assets and the game's truth-ending path, checks DOM/CSP/credential-field boundaries and exits. It disables activation entirely and writes only synthetic state in a unique `.build-cache/ui-self-test-*` directory. It is an offline bridge/DOM check, not human UAT or proof of live model quality. GUI execution requires the environment's normal GUI permission.

No live provider call, credential entry, paid request, distribution signing, notarization, update mechanism or broad platform validation has been performed during engineering.
