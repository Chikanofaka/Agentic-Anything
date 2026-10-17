# Witness Loop v0.3 · HAL local Mac app

A first-playable detective game: read the missing-person brief, overhear an interrupted call, inspect an empty railway platform, meet Lin Wu, question her and submit a HAL-governed verdict. The station, anxious anime character and four inspection views are local bundled artwork. English and Mandarin are supported.

The game runs without a key using **simulated dialogue and real local case state**. The native OpenAI adapter is implemented and mock-tested; no paid call was made during this sprint. Live persona quality is still awaiting an authorized playtest. Human Gate remains DOING, ready for review.

## Launch on this Mac

Double-click `integrations/witness_loop/dist/Witness Loop.app` in Finder, or run from the HAL repository root:

```bash
open 'integrations/witness_loop/dist/Witness Loop.app'
```

The app has already been built. To rebuild after approved source changes:

```bash
bash scripts/build_witness_mac.sh
```

This unsigned development app requires the existing `/usr/bin/python3`; rebuilding also requires the existing Swift/macOS SDK. It records this checkout's absolute path for local saves. It is not a portable installer or notarized release. Run one instance per checkout. Moving the checkout requires rebuilding.

Choose a language and detective name, then **进入车站 / Enter the station**. Continue the narrator caption to reach the empty platform. The four numbered hotspots open the clock, red fabric, folded ticket and train trace. Looking at the scene grants no evidence; inspecting does. **Approach the dispatcher** brings Lin Wu into the same scene. Read her caption, click **Continue**, then type. Free conversation costs no case actions; investigation questions show confirmation before spending one of six. The API counter is separate.

Conversation history and the evidence notebook remain available during dialogue (buttons or **Alt/Option+H**, **Alt/Option+E**). Tab navigates controls; Enter activates a focused button or sends a message, Shift+Enter inserts a line break, Escape closes an inspection or drawer. Reduced-motion system settings are respected. The app's minimum native window frame is 800×620; compact verification uses 820×700 content size.

For the three outcome walkthroughs, actual app screenshots and remaining human checks, see [visual UAT](../../engineering/WTL03_UAT.md). These outcomes are bounded MVP deductions; the clock/call link is an investigative hypothesis, not proof of the full director story.

## Native provider activation

**Connect OpenAI** opens an AppKit secure credential field and explicit consent. API access is separate from a ChatGPT subscription. Enter credentials only there, choose a model your account can access, and review the request limits. Activation itself makes no request. Subsequent messages use up to two requests each, with 20 requests per activation; this is not a monetary cap. A classifier-recognized case follow-up may consume one request before confirmation. Its classification is reused for the same confirmed message.

The key stays in native process memory for this session and is cleared on disconnect or quit; it is not passed to JavaScript, Python or saves. The fixed OpenAI Responses endpoint, no-redirect policy and local-only renderer remain in place. Provider failure leaves the dialogue uncommitted. Known character violations are replaced by authorized local dialogue with an explicit fallback receipt. Text-pattern validation is not a guarantee against every semantic contradiction. Do not enter a key unless you intend to authorize real provider use.

## Saves and character authoring

Active save: `integrations/witness_loop/data/session-v2.json` (plaintext, mode 0600, Git-ignored). When it is absent, a recognized valid v1 `session.json` is migrated while leaving the original bytes untouched. Old automatically granted clock/ticket clues are marked `LEGACY_V1_ACQUIRED`, never presented as new inspections. Old progress, conversations, commitments and endings survive. Invalid or unsupported saves fail closed without replacement. Preserve the file and diagnose before starting a separate case.

**Attributed memory** shows actual session records. **Export case** uses a native Save panel to write a JSON bundle containing `state_json`, readable `user_md` and `receipt_json`. Restart/clear replaces only the active v2 case after confirmation; original v1 backups and previous exports remain. Exported `user.md` is data, not a trusted instruction source. No real player save was used for engineering tests.

Canonical authoring files are `source/identity.md`, `memory.md`, `user.md`, `narrator_intro.md` and `case_brief.md`. Build-time compilation extracts reviewed sections into `runtime/trusted_adapters/witness_character.json`. The build and turn receipts identify the effective character digest and source hashes. The running app reads the compiled artifact, not arbitrary Markdown. Rebuild and relaunch to apply reviewed edits. `python3 scripts/compile_witness_character.py --check` rejects a stale artifact; the build regenerates it. Changing canonical identity requires an explicit code review; English opening translations must be reviewed alongside Mandarin opening changes. Full director-only story is excluded from the model projection and app bundle.

Original v0.1 sources are preserved in `reference_v01/`; duplicate authoring copies outside this directory are archival and cannot change runtime behavior. See [source provenance](SOURCE_PROVENANCE.md) and [art provenance](ASSET_PROVENANCE.md). The supplied moodboards remain local review material and are excluded from the app/source delivery.

## Shared developer pathway and verification

**Path A · Developer package** exposes the reviewed README, Skill, manifest and declarative source entry without a HAL key. The source implementation is in `runtime/hal_core/interactive.py`, `runtime/trusted_adapters/`, `runtime/fixtures/witness/`, `native/` and `ui/`. Open the HAL root in your IDE. Both pathways use the same registered domain contract; importing a random ZIP does not execute its code or turn it into a supported domain.

```bash
bash scripts/verify_witness_local.sh
'integrations/witness_loop/dist/Witness Loop.app/Contents/MacOS/WitnessLoop' --ui-self-test
python3 scripts/package_witness_source.py
```

The first command runs Core/security regressions, both original specialist domain executions, a negative provider preflight, then rebuilds and runs native mocked-provider tests. The second opens the actual WKWebView with activation disabled, creates synthetic isolated saves, exercises the UI/native/Core path and saves screenshots under `.build-cache/`. It never loads the player's save. The final command creates `dist/HAL_Witness_Loop_v03_Source.zip` from explicit source roots, excluding saves, keys, caches and supplied reference images.

See [engineering receipt and file-by-file changes](../../engineering/WTL03_RECEIPT.md), [implementation decisions](../../engineering/WTL03_DECISIONS.md) and [native boundaries](native/README.md). No live-model certification, arbitrary-harness activation, public publication or distribution rights are claimed.
