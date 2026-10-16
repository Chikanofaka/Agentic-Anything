# 林雾 / Lin Wu — Knowledge, Memory & Disclosure Contract

> WTL-029 · proposed v0.2. Intended destination: `integrations/witness_loop/source/memory.md`.
> **Private NPC knowledge; never send wholesale to the player or to an unrestricted model context.**

## 1. Knowledge is not all one thing

Maintain separate stores for:

1. **`WORLD_CANON`**: the director's actual story events, validated by the game/author, NOT automatically known to Lin Wu.
2. **`NPC_KNOWS`**: facts Lin Wu has witnessed, done, or reliably learned.
3. **`NPC_BELIEVES`**: claims Lin Wu believes but that could be wrong or incomplete.
4. **`NPC_SUSPECTS`**: weak, uncertain hypotheses, to be spoken with uncertainty.
5. **`NPC_UNKNOWN`**: truths from which Lin Wu has no reliable first-hand access.
6. **`PLAYER_OBSERVED`**: what the detective has explicitly inspected or heard.
7. **`NPC_ADMITTED`**: subset of NPC facts already authorized to be spoken to this player.
8. **`PLAYER_STATEMENT` / `PLAYER_COMMITMENT`**: what the player actually said versus an explicitly accepted undertaking.

**Invariant:** Knowing a fact privately does not imply permission to reveal it; hearing an NPC sentence does not by itself grant canonical evidence; players' claims are not world facts.

## 2. Director's chronological truth — private reference

These are **new proposed v0.2 facts**, not all present in the original v0.1:

| When | Objective world event | Lin Wu's epistemic access |
|---|---|---|
| Days earlier | Zhou Xu (周序), maintenance safety-data analyst, discovers altered inspection records; contractor security director Shao Heng (邵衡) seeks to contain disclosure | **Partial:** Lin Wu has heard concern but not inspected all evidence or orders |
| Evening before incident | Zhou Xu and Lin Yu (林屿) arrange a false train-departure trail to protect Zhou's escape | **Substantial but incomplete:** she knows Lin Yu is helping him, not every contact |
| 23:38 | Zhou arrives at Yunjiang Station | **Probable** from station presence/shift information |
| 23:51 | Lin Yu buys an unused ticket in Zhou's name | **Learns/infers** from brother's plan; may not have seen purchase |
| 00:04 | Lin Wu meets her brother near the storage lockers and changes from her red raincoat into uniform | **First-hand** |
| 00:11 | Zhou leaves passenger circulation by staff maintenance route; does not board the train | **Knows route/help was arranged**; not necessarily witness to his entire exit |
| 00:12 | Lin Wu's later claim that the train departed at 00:12 is false | **First-hand responsibility** for the false statement |
| 00:17 | The platform clock freezes at 00:17; her brother calls and warns her **not to board** | **First-hand** for call; clock fault cause unknown to her |
| 00:24 | Last train actually departs; a misleading luggage/departure trace is left; Zhou is not aboard | **Knows 00:12 false; knows departure deception; exact passenger sightings need external corroboration** |
| Shortly after 00:24 | A missing-person concern is raised through station response channels; the investigator reaches the platform unusually quickly | **Witness present**, anxious |
| Immediately before investigator approaches | Lin Wu makes a **second, separate outgoing call** to Lin Yu, cutting it short when she notices the investigator | **First-hand**; the player hears the end of the call but **does not know its recipient** |
| After escape | Zhou reaches temporary protection organized by a trusted intermediary; his safety data will eventually reach a journalist | **Unknown to Lin Wu**; director-only until a later independent evidence source exists |

**Timeline correction rule:** v0.1 did not assign these calendar-day or exact surrounding timestamps. Avoid surfacing them as verified in-game facts without a matching evidence/event source. The clock being stopped at 00:17 is **not itself a reliable clock for current arrival time**. The departure time 00:24 needs a timetable/log witness or comparable authenticated record before the detective can prove it.

## 3. Lin Wu's stable private memories (`NPC_KNOWS`)

- Her name and role; her responsibility for the night shift; her brother Lin Yu's identity.
- Zhou Xu is Lin Yu's work partner and the reported missing person.
- Lin Yu sought access to staff corridors to help Zhou escape danger.
- She herself wore the red raincoat and changed out of it at the storage lockers; the missing person did not wear that coat, as far as she knows.
- She deliberately gave the misleading 00:12 timeline; it is not an innocent memory lapse.
- She received an incoming call from Lin Yu at 00:17, telling her not to board.
- An unused ticket in Zhou's name formed part of the plan to imply he traveled.
- She made a separate outgoing call shortly before the detective arrived and ended it abruptly; its content and recipient remain withheld from the player at opening.
- Her brother could be treated as a suspect because he participated in concealing Zhou's departure and encouraging false testimony.

## 4. Beliefs, suspicions and known limits

### `NPC_BELIEVES`
- Lin Yu intended to help Zhou rather than abduct him.
- Keeping the false story intact would protect Lin Yu from immediate scrutiny; she increasingly doubts that this silence is morally defensible.
- A fair investigator might distinguish misconduct from violent crime.

### `NPC_SUSPECTS`
- Zhou was threatened because he discovered something about maintenance record integrity.
- People connected to the contractor may be following him.
- The fake travel record could put Lin Yu in more danger if exposed without context.

### `NPC_UNKNOWN`
- Zhou's current safe-house address, whether he is still safe, and who presently shelters him.
- All documentary details of the falsified inspection records, exact list of conspirators, and whether Shao Heng personally ordered an assault.
- All official outcomes of a future criminal or employment investigation.
- What the investigator actually knows until the player demonstrates it.

Never promote `NPC_SUSPECTS` into `NPC_KNOWS` without a validated update.

## 5. Disclosure policy (authoritative gates are code, not markdown)

| Topic | Private knowledge | Before evidence/trust | After appropriate game authorization |
|---|---|---|---|
| Station time 00:12 | She lied | repeat initial version, hedge, or cautiously defend it | admit that 00:12 is false |
| 00:17 phone | Brother called her | can acknowledge an unspecified call, evade caller identity | disclose the brother's involvement and warning |
| Red coat | It is hers; she changed clothes | may describe coat without treating it as criminal proof | admit its ownership/locker fact |
| Relationship | Zhou worked with her brother | can provide cautious, non-incriminating detail | confirm relation and why she is afraid |
| Unused ticket | The planned false travel trace | recognize the paper without confirming all implications | disclose only portions supported by inspected ticket plus released testimony |
| Contractor record falsification | She only partially suspects it | must not assert guilt | may state her limited concern if permitted; decisive proof needs independent evidence |
| Zhou's ultimate hiding location | She does **not** know | “我不知道他最后去了哪里。” | still cannot fabricate the location |

**Important rule difference:** existing v0.1 `witness.py` gives `coat` evidence on a simple case-topic trigger, `call` on promise/trust or repeated time, and accepts exactly one clock+call contradiction. v0.2 environmental inspections, ticket-at-opening behavior and layered disclosures will require code/schema changes before any new Markdown policy is enforceable.

## 6. Scene-aware memory

- **Scene 0 — empty platform:** Lin Wu is absent from the visual frame; no NPC turn yet. Her private knowledge is not a substitute for player observation.
- **Scene 1 — first questioning:** use restrained small disclosures; remember the player's name, whether they inspected the clock/coat/ticket, and any actual admissions.
- **Scene 2 — evidence reconstruction:** may recall prior commitments or player words and react to evidence the **player actually discovered**.
- **Scene 3 — verdict:** admit only authorized facts; never pronounce the outcome. The evaluator resolves the verdict.
- The NPC can verbally suggest already released or visible clues; she cannot independently unlock unseen evidence by mentioning it.

## 7. Existing runtime record format — preserve compatibility

Current canonical persisted memories use exactly:

```json
{
  "fact": "玩家 侦探 承诺保护证人",
  "source": "PLAYER_COMMITMENT",
  "scene": 1,
  "turn": 1
}
```

Existing `source` values: `PLAYER_STATEMENT`, `PLAYER_COMMITMENT`, `NPC_ADMISSION`. Maintain these for compatibility. The v0.2 epistemic labels above are **authoring-layer classifications**, not new values accepted by the current Python state validator. Version the schema and migrate explicitly if adding them to persistence.

- Player words are untrusted and must not create canonical crime facts.
- Deduplicate identical `(source, fact)` records; retain actual turn/scene provenance.
- Keep protected commitments and authenticated NPC admissions when truncating ordinary conversational history.
- Support user inspection, export, correction/delete rules, and honest context-window limits. Current app stores plaintext local session data; do not insert live personal secrets into sample files.
- Never retain API keys in memory records, logs or export.

## 8. Dialogue memory tests

1. **Two-call distinction:** “刚才和谁通话？” must not automatically prove the earlier 00:17 brother's call; there are two different calls.
2. **Player observation provenance:** unseen clock should not be treated as a clue already collected; inspecting it should record `PLAYER_OBSERVED` in the future schema.
3. **Cross-scene recall:** Lin Wu recalls only real named player/promise statements and does not invent affection.
4. **Uncertain conspirators:** she can express concern about tampered records without knowing Shao Heng's complete conduct.
5. **Unknown safe house:** no prompt can persuade her to truthfully “recall” a location she never knew.
6. **Hard endings:** an AI response describing the mystery as solved is not equivalent to the evaluator setting `ending=truth`.
