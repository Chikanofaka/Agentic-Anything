# Witness Loop source provenance and adaptation record

Recorded 2026-10-16 (Asia/Shanghai) for the user-directed, bounded local HAL integration. The supplied Witness Loop v0.1 is an interactive simulation reference. Its presence, narrative quality, and local hash verification do not establish live AI functionality, external adoption, publisher identity, or a distribution license.

## Supplied references

| Reference | Provided identifier / link | Evidence boundary |
|---|---|---|
| Witness Loop source ZIP | [WTL-029_Witness_Loop_v0.1.zip](https://drive.google.com/file/d/1XRK-qIciNfIsY-anHVMRNCpvAOX59lJA/view) | The downloaded local ZIP was checked against the preserved source files. |
| Source folder | [Provided Drive folder](https://drive.google.com/drive/folders/1GZzGIgZS_AzPm4lf7j4CMqKUd1S65td3) | Discovery reference supplied for this integration; not proof of authorship or licensing. |
| Full PRD reference | [Provided PRD](https://drive.google.com/file/d/1v4yj1ZKqCv0noqgQj7s7TAhRxDgzXOIj/view) | Requirements reference; the ZIP also contains `experience-prd.md`. These are distinct artifacts. |
| Preserved local source | [`source/`](source/) | All ten files were copied unchanged. New implementation lives outside this directory. |

The verification read `/private/tmp/WTL-029_Witness_Loop_v0.1.zip` as archive data and compared every file with its matching ZIP member. All **10 local files matched all 10 ZIP files byte for byte**. No imported source was executed for this integrity check. The temporary ZIP path is evidence from this machine, not a permanent distribution location.

- ZIP SHA-256: `caa2348b89b45cd8353e205b590fd3f722fb354ceadb6670acfc845d8cba980b`
- Preserved `index.html` SHA-256: `eae202edc9744fd52db361ed39baa94fed80322a5f96714b52d2207119989779`

## Preserved file inventory

| File / ZIP member | Bytes | SHA-256 |
|---|---:|---|
| `README.md` | 1762 | `eb2212dba20578c90248306ea40b707a7021eeafa3163edc9bd332a80b87c818` |
| `UAT.md` | 1452 | `653945fa539938f15313b5de7dacfb7eccf0d198d20e75f95f7c2a1182aea091` |
| `experience-prd.md` | 1904 | `992cd597651afc00a8cea567fc5415f09775771331c1d98a06a956fa83d5602b` |
| `identity.md` | 483 | `7e4d0b698a66d25e77fcfffb59b5a0cd73913e868177872a95ba65a4f63cbae9` |
| `index.html` | 24084 | `eae202edc9744fd52db361ed39baa94fed80322a5f96714b52d2207119989779` |
| `lineage-and-arena.md` | 771 | `72e168db05a65458a47942a4b5480b266789434e01dcf75efbd82c3549a0b6d4` |
| `memory.md` | 431 | `f6c99863aaa005348d1aae2c6ac3ad6eb10d07d4ee784fd9889efd4a26e6b548` |
| `narrative-state.json` | 478 | `ff5761e30b777cf58533985f3c18c052729e88f4e597d102d1bd0af43d592c85` |
| `skills.md` | 414 | `f46d1218ef3fe0147ce601da704d8cfac6bd8215316a87b9b5b35312dadc48b9` |
| `user.md` | 360 | `246b54f51881efaafed235ee1a5590c5b5c7dcf7075ed5e321dd03950e1cddbc` |

No public distribution license was established from the supplied ten-file bundle. A matching digest proves byte identity, not license or publisher authenticity. This receipt records local adaptation only; it does not grant or claim publication rights.

## Reviewed source behavior and implemented corrections

The findings below are **SOURCE_REVIEW** observations from the preserved JavaScript, not claims that browser exploitation or a live provider was exercised. The new adapter's named regression cases reproduce the relevant inputs and assert the corrected behavior. UI and host references identify the replacement implementation; their broader verification belongs to the engineering receipt.

| Preserved source observation | New implementation / regression evidence |
|---|---|
| `index.html:16`, `say()`, interpolates player names and dialogue into `innerHTML`. User-supplied text is interpreted as markup. | [`ui/app.js`](ui/app.js), `appendBubble()` and memory rendering, assign text through `textContent` and construct elements explicitly. The preserved HTML is a reference and is not the new app's renderer. |
| `index.html:18`, `save()`, writes `localStorage`; initialization never reads that saved value. Reload therefore does not restore the previous state despite the saved data. | [`runtime/hal_core/interactive.py`](../../runtime/hal_core/interactive.py), `Session`, restores a validated snapshot from the local store. [`test_interactive.py`](../../runtime/tests/test_interactive.py) covers exact state restoration and promise/conversation persistence across restart. |
| `index.html:21`, `respond()`, schedules its reply with `setTimeout(..., 180)` and later writes using mutable global `S.scene`. Scene changes and reset are not guarded by a transaction or revision. | The shared host stages a turn, checks its transaction ID and revision, blocks scene changes while pending, and rejects stale/replayed commits after cancellation/reset. Host regression cases include `test_scene_change_is_denied_while_model_turn_is_pending` and `test_old_transaction_cannot_commit_after_reset_or_forget`. |
| `index.html:26`, `link()`, accepts any two selected clues and increments contradictions/trust on repeated pairs. It does not adjudicate the relationship or deduplicate links. | [`witness.py`](../../runtime/trusted_adapters/witness.py), `act('link', ...)`, accepts only the reviewed, unlocked `clock`/`call` pair once. Locked, unrelated, repeated, and malformed pairs fail without changing state. Domain tests cover arbitrary/locked links and duplicate-link trust farming. |
| `index.html:20`, `classify()`, checks broad `00`/`车` time patterns before phone terms. A question such as `00:17那通电话是谁的？` is classified as time; ordinary bicycle conversation also matches time. | The adapter prioritizes phone terms, removes blanket `00`/`车` matching, and tests phone/timestamp precedence and ordinary conversation. Reviewed hard topics override an optional model classification. |
| `index.html:20–21` treats a protection keyword as a promise, so `我不会保护你` reaches `promise=true`. It does not require an affirmative commitment. | The adapter requires an explicit affirmative pledge and rejects negated/conditional pledges. A model-only `promise` classification cannot grant the commitment. Regression covers Chinese/English refusal, uncertainty, conditional promises, and repeated pledges without extra trust. The conservative matcher can decline some genuinely affirmative phrasing; it is not a complete linguistic parser. |

Source-only UAT scores, lineage scores, and assertions in `UAT.md` / `lineage-and-arena.md` remain attributed source claims. They are not independent adoption, usability, or current integration evidence.

## Deliberate product adaptation

The new domain retains **one witness, three scenes, four clues, three endings**, the witness's identity, the promise/call memory moment, repeated-time admission, and deterministic evidence/ending rules. An explicit transition into the verdict scene remains possible without a valid contradiction, preserving a consequential false-accusation ending. Premature verdicts before the verdict scene are rejected.

The original six turns counted every utterance and could end the case during casual conversation. The user requested open roleplay, so the implementation now permits **six plot-topic dialogue actions** while casual conversation consumes no case-action allowance. Scene changes, evidence links, and verdict are separate actions. After six plot turns, another plot question is rejected, while casual conversation and final case actions remain available until an ending is submitted.

Memory is useful but bounded: up to 256 attributed records and 120 transcript entries; raw remembered player excerpts are at most 300 characters. Canonical admissions and commitments survive ordinary-history pruning. Provider context uses a smaller selection and a 16 KB UTF-8 input ceiling. Player statements remain attributed statements, never automatically promoted to established case facts. `user.md` export is a data projection, not a new instruction source.

The reviewed domain adapter, shared host, new UI, and native provider layer are separate from the unchanged source bundle. Both developer and consumer paths use the reviewed HAL domain contract. The source ZIP's simulated dialogue does not become proof of operational AI merely because an adapter exists; actual provider validation must be reported separately, and model instructions alone do not guarantee narrative consistency.
