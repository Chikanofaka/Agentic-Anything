# Investigator / Player — Starting Profile & Knowledge Ledger

> WTL-029 · proposed v0.2 · intended destination: `integrations/witness_loop/source/user.md`
> **Player-visible onboarding contract.** Nothing in this document grants the detective facts that have not yet been observed.

## 1. The player is a detective, not an omniscient reader

- **Role:** investigator responding to a concerning missing-person report at fictional **Yunjiang Railway Station** shortly after the last train has departed.
- **Player-selected name:** `{{PLAYER_NAME}}` — filled during onboarding; default is `侦探`.
- **Questioning approach:** `empathetic` / `direct` — chosen during onboarding; this is style, not an automatic finding of truth.
- **Mission:** determine whether Zhou Xu (周序) boarded the last train, reconstruct the timeline and his last verifiable movements, test witness statements against observed evidence, and submit a defensible finding.
- **Your authority:** inspect scene objects, question a witness, form evidence links and submit a verdict. You cannot directly edit canonical evidence, trust, fear, scenes, NPC memory or endings.

## 2. What the player actually knows before entering the platform

**Reported facts** (may themselves be incorrect):

1. Zhou Xu, a railway-associated worker, cannot be accounted for and has been reported missing.
2. His disappearance is being associated with the final train of the night, but whether he boarded is **not yet established**.
3. The duty dispatcher Lin Wu is an important potential witness.
4. It is rainy and late; the scene may still contain useful traces.
5. Your objective is investigation, not prosecution of a predetermined suspect.

**Not known at game start:** Lin Wu lied about 00:12; the existence, time or origin of the earlier 00:17 call; her brother's name and participation; the coat's ownership; who bought or used the ticket; whether Zhou is alive; whether any crime occurred; whether the last train departed at 00:12, 00:17 or later.

### Observed immediately during opening narration

- The investigator hears the **end of a woman's hurried telephone conversation** near the platform and hears it stop abruptly as the investigator approaches.
- This is an **unnumbered, unverified auditory observation**: the player does not yet know who called, what exact time the call began, or whether it matches any later-discovered historical call record.
- A fading red railway light may be visible at the far track; it is only a **departure-like trace**, not proof that Zhou was a passenger.

## 3. Environment-only observation phase (before Lin Wu appears)

Only after a deliberate click/inspection may a visual object be added to the player's evidence notebook. No visual easter egg should silently become a collected clue merely by appearing in a background image.

| Object and visual location | Before inspection | After clicking / zooming | What must remain unproven |
|---|---|---|---|
| Platform clock, high on right-side support beam | An old clock in the distance | It is stopped and visibly reads **00:17**; `clock_observed=true` | That the train departed at 00:17, or that Lin Wu lied |
| Red cloth/raincoat by locker-side bench | Red fabric, partly obscured | Red fabric/raincoat fibers; `coat_observed=true` | Who owned or wore it, whether Zhou wore it |
| Folded paper on bench | A folded ticket-like object | Unused ticket printed **周序 / Zhou Xu**, route/date legible; `ticket_observed=true` | That Zhou never physically boarded; unused ticket alone doesn't prove absence |
| Tiny receding rail tail light | Far red glow in rain | Visual record of a train-like departure trace | Identity of any passenger; exact departure time |
| Interrupted woman's voice | A hurried call, no face shown | An overheard phone event entered in observations | Caller identity, 00:17 timing, phone contents |

**Asset caution:** the provided mood-reference photographs do not themselves show the specific required in-game clock time or fictional ticket name. Build accurate interactive prop images or HTML close-up overlays rather than misrepresenting reference photographs as evidence.

### Scene transition

The player chooses **Approach the witness / 走近证人**. Only then does Lin Wu's portrait enter the same scene composition, with its visual evidence hotspots still accessible.

The player is permitted to approach before inspecting every object. The game must preserve this choice and make it clear which observations were missed, without quietly handing the player those facts.

## 4. Evidence ledger — proposed v0.2, not yet the current runtime schema

Record separately:

```yaml
player_profile:
  name: "{{PLAYER_NAME}}"
  questioning_style: empathetic  # or direct
  role: investigator
knowledge:
  confirmed_reported_facts: ["Zhou Xu reported missing", "Lin Wu is a witness"]
  observed_environment: []       # append only after inspection
  reported_testimony: []          # what NPC said, not yet proven
  authenticated_evidence: []      # evidence accepted by evaluator
  hypotheses: []                  # player conjectures are never canon facts
  supported_deductions: []        # evaluator-approved relationships
  unresolved_questions: ["Did Zhou Xu board?", "What occurred at 00:17?"]
resources:
  case_actions_max: 6
  case_actions_used: 0
```

Current HAL `witness-state/v1` actually stores `player`, `style`, `scene`, `case_turns`, `asked`, `clues`, `links`, `trust`, `fear`, `promise`, `memories`, `transcript`, `ending`, `revision`. The richer ledger above requires an explicit v0.2 schema migration or compatible sidecar; **do not replace a persisted v1 session JSON with this YAML**.

## 5. What kind of detective can the player be?

- **Observation-first:** inspects everything, then asks targeted questions.
- **Interrogation-first:** approaches Lin Wu quickly and risks missing objects; can later revisit environmental evidence if the director permits.
- **Relationship-first:** builds trust through personal conversation; this is meaningful optional play but not automatic case completion.
- **Speed-run / developer player:** already knows hidden truth outside the fiction; the game may reward correct evidence but must not presume their character knows facts never encountered in play.

No archetype is auto-assigned. Player choices generate the profile.

## 6. What the UI should show the player, and when

### Before meeting Lin Wu

- Case briefing and immediate mission.
- Environmental inspection scene with five potential visual/auditory hints.
- Evidence notebook separating **Seen**, **Inspected**, **Testimony**, **Verified** and **Hypothesis**.
- No pre-filled “00:12 is a lie” objective.

### During interrogation

- Lin Wu's line appears with her portrait/subtitle, then a player input turn; both parties' turns remain reviewable in a sidebar transcript.
- Player can click an earlier line and see which scene/turn produced it.
- Case-action remaining count is distinct from ordinary conversation and provider API request count.
- Uninspected objects remain visually reachable; reading history is not an action cost.
- Distinguish the player's selected hypothesis from the adjudicated outcome.

### At case resolution

- Show supported chain of evidence, missing assumptions, credibility of the deduction and why the result was awarded.
- Respect limited player knowledge even if the author knows the entire plot.

## 7. Data privacy and real user profile safety

- This is a fictional detective profile, **not** a profile of the human operator. No real name, API credential, address or personal history should appear in the repository starter file.
- Player input is only `PLAYER_STATEMENT` unless a contract explicitly accepts a `PLAYER_COMMITMENT`; a statement is not a case fact.
- The Mac build currently saves local session JSON under `integrations/witness_loop/data/session.json` as plaintext with restrictive local file permissions; do not copy actual saves into public Git. Exports may remain on disk even after game reset.
- The native OpenAI connection may transmit selected conversation and evidence context. Show that disclosure during onboarding.

## 8. State and experience UAT

1. Fresh player can explain **who disappeared** and **their purpose** after the case brief, without having learned secrets about Lin Yu.
2. The player cannot cite “00:17 on the clock” as collected evidence before they actually inspect it.
3. The ticket close-up names **周序**, not an unrelated real-world transit provider.
4. Clicking **Approach** without looking around is allowed, but the evidence log accurately reflects missed items.
5. The player who notices a last train light cannot automatically prove Zhou was on it.
6. Past dialogue and item-inspection history remain readable and properly timestamped/attributed.
