# WTL-029 · Lin Wu Story & Memory Source Pack — v0.2 (DRAFT)

**Ready-to-copy Markdown files; not an automatically installed or live-tested software update.**

## Contents

| File | Intended role | Spoiler level | Replaces / creates |
|---|---|---|---|
| `identity.md` | Lin Wu's persona, visual appearance, values, behavior and constraints | Private NPC | Replace `integrations/witness_loop/source/identity.md` |
| `memory.md` | Lin Wu knowledge, belief, uncertainty and disclosure/memory contract | **Private NPC** | Replace `integrations/witness_loop/source/memory.md` |
| `user.md` | Detective onboarding and player-visible starting knowledge / observation ledger | Player-safe | Replace `integrations/witness_loop/source/user.md` |
| `narrator_intro.md` | Opening captions, empty platform investigation, entrance and dialogue UX | Player-safe | Add `integrations/witness_loop/source/narrator_intro.md` |
| `case_brief.md` | Full director-only plot, timeline, actors, solution, ending rules, implementation gap | **Director spoilers** | Add `integrations/witness_loop/source/case_brief.md` |

## Grounding and intentionally new fiction

- **Preserved v0.1 facts:** Lin Wu is a night-shift dispatcher protecting her brother, original 00:12 testimony is false, her brother called her at 00:17, the red raincoat belongs to her, the missing person is her brother's colleague, Lin Wu cannot disclose the missing person's ultimate whereabouts.
- **New director-approved-for-drafting (not yet repository canon):** Yunjiang Station; Lin Yu, Zhou Xu, Shao Heng; maintenance-inspection-record conspiracy; escape via maintenance corridor; exact 00:24 departure; an off-screen **second** phone call just before the player arrives; protection/intermediary and safe house.
- **Source distinction:** director-only knowledge is **not** equivalent to player/NPC knowledge. The `case_brief.md` file includes spoilers; never load it wholesale as a model persona instruction or initial user brief.

## Local install into an existing Mac repository

From a clean Git checkout such as `~/Desktop/HAL-P2D-001`, first create a backup branch or backup copies. Suggested read-only diagnostics:

```bash
git status --short --branch
git log -1 --oneline
```

For simple manual copy in Finder, open your repository's `integrations/witness_loop/source` folder. Copy the five `.md` files into it and agree to replace **only** `identity.md`, `memory.md` and `user.md`. The other two are new. Keep `WTL-029_Witness_Loop_v0.1/` unchanged as the baseline.

For Terminal copy, after extracting this pack and backing up existing files:

```bash
cd ~/Desktop/HAL-P2D-001
# Replace /path/to/pack with your actual extracted pack directory.
cp /path/to/pack/identity.md integrations/witness_loop/source/identity.md
cp /path/to/pack/memory.md integrations/witness_loop/source/memory.md
cp /path/to/pack/user.md integrations/witness_loop/source/user.md
cp /path/to/pack/narrator_intro.md integrations/witness_loop/source/narrator_intro.md
cp /path/to/pack/case_brief.md integrations/witness_loop/source/case_brief.md

git diff --check
git status --short
```

**Do not paste the entire story into `runtime/trusted_adapters/witness.py` or `REPLY_INSTRUCTIONS`.** That would leak future facts and weaken the evidence gates.

## Public repository spoiler warning

`case_brief.md` contains the **entire solution**. If you copy it into your public `HAL-P2D-001` GitHub repository and push, any visitor can read the ending. For a future publicly distributed mystery, keep the director-only truth in an appropriately separated/private authoring or trusted-content location, or accept that an open-source repo exposes spoilers. A filename such as `case_brief.md` is **not** a secrecy or access-control mechanism.

## Critical runtime limitation

The current game does **not** dynamically read these Markdown files as its authoritative live character prompts. In the October 16 HAL integration, game rules and compact model context are generated primarily by `runtime/trusted_adapters/witness.py`, the native application and `ui/app.js`. Changing these files gives Codex an aligned **source-of-truth design pack**, not a functioning new sequence of scenes or memory system.

In particular, these require engineering changes before they work:

1. Empty-station clickable clue scene and zoom UI.
2. Lin Wu entering after environmental observation.
3. A distinction between `visible`, `inspected`, `collected`, `authenticated`, and `linked` evidence.
4. The additional ticket, train departure and two-call knowledge/event contracts.
5. Scene/turn/ending acceptance criteria and a safe fact-release projection.
6. Long conversation transcript browsing and UI turn sequencing.

No source code is included in this pack. The current run remains a scripted deterministic state machine offline and LLM-supported dialogue when a user-authorized OpenAI API key is activated.

## Suggested next Codex prompt (after narrative approval)

> Review the five WTL-029 v0.2 files under `integrations/witness_loop/source/` and compare them with the current `witness-state/v1`, `runtime/trusted_adapters/witness.py`, `integrations/witness_loop/ui/`, and native host. Treat `case_brief.md` as director-only. Propose a staged implementation plan that preserves existing test baselines and never exposes hidden spoilers to the player or model before evidence release. Implement a Scene 0 environmental inspection with tested hotspots, a distinct later phone call, validated player-knowledge state, and Lin Wu's sequential arrival/interrogation. Explicitly resolve the pre-existing ticket unlock and contradiction/timeline logical gaps. Run regressions and demonstrate a no-key player UAT; do not push the public repository or use a live API key without authorization.

## Approval checkpoint

Before implementation, settle: exact date/location, newly proposed names and conspiracy, final hairstyle, post-departure arrival framing, second-call timeline, whether 00:24 is independently provable, and whether v0.2 changes the current three-ending evaluator. Each is marked as a proposed change, not assumed already implemented.
