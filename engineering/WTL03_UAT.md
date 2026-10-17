# WTL-029 v0.3 · reproducible visual UAT

Date: 2026-10-17, Asia/Shanghai. Human Gate: **DOING / ready for human review after final verification**. This is an implemented local app, not a new PRD or a standalone mockup.

## Reproduce safely

From the HAL repository root:

```bash
bash scripts/verify_witness_local.sh
'integrations/witness_loop/dist/Witness Loop.app/Contents/MacOS/WitnessLoop' --ui-self-test
```

The GUI command opens the actual native WKWebView and uses private JSONL communication with the bundled HAL Core. It disables provider activation and uses a unique synthetic save directory under `integrations/witness_loop/.build-cache/`. Each run writes actual WKWebView PNG captures into a new `v03-ui-smoke-UUID/` directory. It never loads or resets the player's data. The screenshots are application-content captures, not images generated to resemble an app. They omit the native window title bar.

Final GUI verification: **PENDING_FINAL_GUI**. Core: 287 passed; native mocked-provider self-tests: 52 passed. See [receipt](WTL03_RECEIPT.md) for evidence and boundaries.

## Acceptance evidence

| Requested behavior | Verification and practical limit |
|---|---|
| Case brief → narrator → empty platform → Lin Wu | Real native phase sequence; no initial acquired clues; input disabled until entrance caption is acknowledged. |
| Clock, red fabric, ticket, train trace | Four local image-backed hotspots; each actual click opens its matching observation. Clock reads exactly 00:17; fictional ticket reads 周序 / ZHOU XU. |
| Inspection updates only observed evidence | Native state assertions plus domain negative tests. Visibility alone does not grant a clue. Cloth ownership and train departure time are not inferred from appearance. |
| Anxious anime dispatcher | Actual screenshot review: silver hair, gold eyes, railway cap, dark uniform, tense posture. Same station background before/after entry. Hit-test assertions check hotspot centers are reachable outside captions. Human aesthetic approval remains pending. |
| Sequential NPC/player turns | Real Continue → input → reply flow, disabled duplicate send, thinking indicator and distinct narrator caption. Offline replies are simulated; provider delay/cancellation uses mocked host tests. |
| History and notebook | Both drawers can open during NPC dialogue; literal HTML-like player name stays text. Evidence flags and provenance are displayed separately. |
| Immutable brother identity | Compiler and reply-validation regressions reject specified English/Mandarin denials or contradictory family statements before storage. This is bounded textual validation, not universal semantic proof. |
| English/Mandarin | English native dialogue flow and saved preference; Chinese opening and bilingual domain tests. Model language mismatch rejection is tested with synthetic replies. Live bilingual quality is pending. |
| Separate budgets | Native free conversation leaves six case actions and API 0/20 untouched. Case questions require confirmation. Mocked and domain tests cover intent proposals, caps, stale callbacks and duplicate requests. |
| Truth / partial / false accusation | All three deterministic outcomes tested in Core; final native smoke traverses all three through the real bridge. No LLM selects the ending. |
| v1 saves | Synthetic exact-byte migration tests preserve old automatic clock/ticket acquisition, progress, memories and endings. Original v1 file survives migration and active-case reset. No real player save was used. |
| Keyboard and compact layout | Focusable hotspots, modal focus restoration, Tab/Enter/Escape/Option shortcuts and reduced-motion styling. Native compact-window check at 820×700. Full VoiceOver audit and wider OS matrix are pending. |

## Actual application screenshots

Final captures are copied byte-for-byte into [wtl03-screenshots/](wtl03-screenshots/):

- [Original text-heavy baseline](wtl03-screenshots/00-baseline.png).
- [Case brief](wtl03-screenshots/01-case-brief.png).
- [Empty platform](wtl03-screenshots/02-empty-platform.png).
- [00:17 clock inspection](wtl03-screenshots/03-clock-inspection.png).
- [Red fabric](wtl03-screenshots/03b-red-fabric.png), [Zhou Xu ticket](wtl03-screenshots/03c-ticket.png), [train trace](wtl03-screenshots/03d-train-trace.png).
- [Lin Wu entrance](wtl03-screenshots/04-linwu-arrival.png) and [sequential NPC caption](wtl03-screenshots/05-npc-caption.png).
- [Conversation and evidence drawers](wtl03-screenshots/06-history-and-notebook.png).
- [Compact window](wtl03-screenshots/07-compact-window.png).
- [Truth](wtl03-screenshots/08-truth-verdict.png), [partial resolution](wtl03-screenshots/09-partial-verdict.png), [false accusation](wtl03-screenshots/10-false-verdict.png).

Artwork sources, generated-image prompts and local-only rights status are in [asset provenance](../integrations/witness_loop/ASSET_PROVENANCE.md). The reference moodboards themselves are not bundled.

## Manual review and outcome walkthroughs

Launch the already built `integrations/witness_loop/dist/Witness Loop.app`. Existing saves resume their actual progress; they do not replay a new-player sequence. To inspect a fresh case without replacing personal progress, use the isolated GUI test above. Starting/restarting inside the normal app replaces its active v2 case only after the UI's confirmation; keep any desired export first.

For a new English case:

1. Enter a name, read the case brief, then Continue through the narrator. Confirm the interrupted outgoing call does not identify the recipient or claim it was the historical 00:17 incoming call.
2. Inspect any objects. Before clicking an object, the notebook must show it as visible/uninspected, with no invented detailed observation. Inspecting costs no case actions.
3. Approach Lin Wu. Read her surprised greeting, then Continue. Ask “How are you feeling?” and confirm the free conversation does not spend a case action. History and evidence remain accessible.
4. Use one of the independent paths below. Click Continue after each NPC response. Confirm each investigation question when prompted.

| Outcome | Reproducible path from a fresh case |
|---|---|
| Truth | Inspect clock. Say “I promise to protect you.” Ask “Who called you at 00:17?” Select clock + historical-call clues in the notebook and test the connection. Use Review the case twice to reach Act 3, then Submit a verdict. Two case actions. |
| Partial | Inspect clock and ticket. Ask “When did the train leave?” then “What about the station clock?” Link clock + historical-call evidence after her revised account. Advance twice, submit. Two case actions; no promise. |
| False accusation | Inspect clock and ticket, approach and acknowledge the intro, advance twice and submit without making the supported connection. Zero case dialogue actions; the premature conclusion produces the false-accusation outcome. |

After the verdict, previously known evidence remains reviewable. New discoveries cannot rewrite the evidentiary basis or ending. The three outcomes preserve the bounded prototype rules; neither a stopped clock nor an unused-looking ticket establishes the entire director narrative.

## Authoring-to-runtime check

Edit the five canonical files in `integrations/witness_loop/source/`, not the archival duplicate. Only reviewed named sections are projected. Run `python3 scripts/compile_witness_character.py --check` to detect stale compilation. Rebuild with `bash scripts/build_witness_mac.sh`, close the previous app process and reopen. Compare the context version/digest in the developer footer, exported receipt and bundled `build-manifest.json`. The personality-edit regression proves a supported authoring edit changes the actual model context. It does not claim the model has been contacted.

Identity changes require explicit canon review; English opening text is a reviewed translation and must be updated with Chinese opening changes. Director-only sections are hashed for provenance but never copied wholesale into model messages or the app bundle.

## Human review still required

- Approve visual tone, clue legibility and narrative pacing on this Mac.
- With separate live-use authorization, enter a key only in the native secure field and evaluate personality, nuanced paraphrases, bilingual dialogue and memory across real provider turns. No paid live calls have been made.
- Exercise native credential entry, export Save panel and confirmation/cancellation manually if desired; automated screenshots do not prove those OS panels.
- Decide reference/derivative distribution rights before publishing; signing, notarization, portability and wider accessibility/platform certification are outside this local sprint.

Review readiness does not authorize publication or advance the Human Gate automatically.
