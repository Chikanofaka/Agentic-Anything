# Witness Loop · HAL local app

This is the first application of HAL to the supplied Witness Loop game. It combines a native Mac host, specialist game UI, the shared HAL Core and a reviewed narrative adapter. Original reference files remain unchanged in `source/`.

The game runs immediately without a key, with **simulated dialogue and real saved state**. The OpenAI request adapter is implemented and tested with synthetic responses; no real credential or billable inference was used during engineering. Live persona quality is not yet verified.

## Open on this Mac

From the HAL workspace root:

```bash
bash scripts/build_witness_mac.sh
```

Then double-click `integrations/witness_loop/dist/Witness Loop.app` in Finder. This development build requires the existing `/usr/bin/python3` and Swift/macOS SDK for rebuilding. It records this checkout's location for saved data. It is unsigned, not notarized and not a portable installer. Rebuild after changing source files.

Choose **开始游戏**, enter a name and play through the short onboarding. Try promising to protect Lin Wu, asking about the 00:17 call, advancing to scene two, connecting the clock and call clues, advancing again and submitting a verdict. Other evidence/relationship paths produce different endings. Casual dialogue does not consume the six plot actions; offline responses remain fixed examples.

For live language, click **连接 OpenAI**. Enter your authorized API key only in the native secure field, choose an accessible model, and read/accept the session request limits. Activation makes no call. The next message can send two paid API requests. A successful response verifies access for that session. Failure leaves the turn uncommitted; you can disconnect and continue offline. Keys are cleared on disconnect or quit and are never saved by the app. Do not paste a key into Codex/chat or the reference HTML.

## Memory and developer pathway

Saved session: `integrations/witness_loop/data/session.json` under this checkout. It contains plaintext dialogue, profile, evidence, provenance and receipts with file mode 0600; it is excluded from Git. **她记得什么** displays admitted memory. **删除全部记忆并重置** clears the active local profile/case after native confirmation. Existing exported copies are not erased. **导出案件与 user.md** opens a native Save panel and writes a JSON bundle containing `state_json`, readable `user_md` and `receipt_json` strings.

An invalid/corrupt save fails closed without overwriting it. Close the app, preserve/rename that save in Finder and reopen to start clean. Moving the checkout requires a rebuild. Run one app instance per checkout: concurrent multi-process editing of the same save is not supported.

**开发者路径 A** displays README, Skill, manifest and source entrypoint without asking HAL for a key. The complete implementation lives in `runtime/hal_core/interactive.py`, `runtime/trusted_adapters/witness.py`, `runtime/fixtures/witness/`, and this directory's `native/` and `ui/`. Open the HAL root in your IDE; use its own approved environment. `main.py` in the domain fixture is a declarative entrypoint marker, not the full game implementation. Import inspection never executes it.

## Verify

```bash
bash scripts/verify_witness_local.sh
```

That runs all Core regression/security tests, asserts the original two specialist CLI outputs and negative provider preflight, builds the Mac app and runs native mocked-provider tests. It makes no provider request. An additional offline GUI integration check is:

```bash
'integrations/witness_loop/dist/Witness Loop.app/Contents/MacOS/WitnessLoop' --ui-self-test
```

The GUI check disables activation and uses isolated synthetic storage under `.build-cache/`. It checks the real JavaScript/native/Core path and rendered DOM. It is not a human playtest or live AI evaluation.

See [the implementation PRD](../../engineering/HAL_WITNESS_TYPE_B_PRD.md), [receipt](../../engineering/WITNESS_INTEGRATION_RECEIPT.md), [source provenance](SOURCE_PROVENANCE.md), and [native boundaries](native/README.md). The reusable architecture is real; arbitrary harness import-and-activation, every provider's credentials, signed distribution and live model quality are not established.
