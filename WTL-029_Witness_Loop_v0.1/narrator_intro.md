# Witness Loop — Narrator Opening & Scene-Entry Script

> Proposed v0.2 · destination: `integrations/witness_loop/source/narrator_intro.md` (new file)
> Player-visible only. **No director spoilers or private NPC thoughts in opening copy.**

## Objective for the introduction

Tell the player **who**, **what**, **where** and **what they are here to accomplish**, while letting them discover **when**, **how** and **why** by investigation. Introduce Lin Wu only after the player has been offered an evidence-only view.

## Screen 0 — Case assignment card

**Header:** `CASE FILE 00:17 — 失踪的乘客`

**Narrator — card copy:**

> 云江站。午夜之后。一名铁路工作人员——周序——突然失去踪迹。最后一班列车刚刚离开，站方尚不能确认他是否登车。
>
> 你是赶到现场的调查员。值班调度员林雾是目前最重要的证人。
>
> **你的任务：**检查现场，核实证词，判断周序是否真的乘上了末班车。不要把怀疑当作证据。

**Primary action:** `进入现场 / Enter platform`

**Secondary action:** `阅读案情摘要 / Read case brief` (reveals only public player starting facts)

## Screen 1 — Pre-approach sound, empty station

**Camera:** a wide, rain-soaked railway platform. Night. A nearly imperceptible train tail light recedes beyond the left-side track; clock high on a support beam; bench ticket in foreground-midground; red raincoat/fabric trace beside lockers. **No person or NPC sprite is present.**

**Sound / caption beat 1 — Narrator:**

> 雨打在空荡的站台上。远处有一抹红光，像是刚离开的列车尾灯，正被雾吞没。

**Sound / caption beat 2 — Woman, off-screen (fragment only):**

> “……我知道。他来得比预想的早。你先别——”

**Sound / caption beat 3 — Narrator:**

> 通话戛然而止。你听见急促的脚步声，却暂时看不到说话的人。附近的站台还没有被封锁，你可以先查看现场。

**Important:** this interrupted, **post-departure outgoing** call is NOT automatically the separate incoming call Lin Wu received at **00:17** from her brother. The player only knows that a woman ended a conversation; the speaker's identity and interlocutor remain to be verified.

**Primary action:** `查看站台 / Inspect platform`

## Screen 2 — Interactive evidence-only platform

**Prompt:** `仔细看看。你看到的是事实，还是对事实的推测？`

**Scene composition (normalized zones for a 16:9 target; test responsive placements):**

| Zone | Visual | On click |
|---|---|---|
| Upper right, x=0.78, y=0.20 | Distant station clock on support beam | Accurate enlarged face reading **00:17**, visibly stopped; record a clock observation |
| Lower right-mid, x=0.70, y=0.70 | Wooden bench with folded paper | Zoom to **周序 / Zhou Xu**, date/route, clearly **unused** status; record a ticket observation |
| Lower left, x=0.18, y=0.76 | Locker-side red fabric/raincoat fragment | Zoom to fibers and cloth; record red-cloth observation without assigning ownership |
| Far left background, x=0.20, y=0.42 | Almost-vanished train tail lamps | Zoom as environmental departure trace; passenger presence remains unknown |
| Ambient audio tag | Abruptly ended conversation | Recall what the player actually heard; no sender number or full call transcript |

**Narrator inspection copy:**

- Clock: “表针停在 **00:17**。它不再走动。这个时间意味着什么，你还不能确定。”
- Cloth: “储物柜附近有一抹红色。仔细看，是一小片潮湿的衣料。”
- Ticket: “纸张折得很紧。放大后能读到‘**周序**’。验票标记缺失——它看起来没有被使用。”
- Light: “轨道尽头的红灯几乎消失了。你只看到有列车离去的迹象，看不到车上的人。”
- Interrupted voice: “刚才确实有人在打电话，但你还没有证据证明她在和谁说话。”

**Buttons:** `放大 / Inspect`, `记入笔记 / Add observation` (or automatic on completed inspection), `查看证据 / Notebook`, `接近证人 / Approach witness`.

**Freedom rule:** `Approach witness` must be available **before** all inspections are complete. Missing an item is a real choice; game should permit reinspection when appropriate instead of backfilling discoveries.

**Accessibility / asset truthfulness:** render the actual `00:17` clue and **周序** ticket label as validated zoom artwork or DOM text overlays. Do not rely on the uploaded atmospheric reference clock (which does not display that exact time), or the photographed Chester City Transport ticket, as literal canonical props.

## Screen 3 — Lin Wu enters (same location, no evidence occlusion)

**Transition:** slow dissolve or short animation; camera framing unchanged. Lin Wu moves into the central safe area **without covering the upper-right clock, right-side ticket or left-side red fabric**. Her eyes flick toward the investigator and she puts away her phone.

**Narrator caption:**

> 一名穿深色制服的年轻调度员从站台尽头走来。她试着保持镇定，却在看见你时不自觉地攥紧衣袖。

**Lin Wu — first spoken line (only after narrator finishes):**

> “你来得比我预想得早……我是林雾，今晚值班的调度员。关于周序失踪的事，我会回答我知道的。”

**UI:** an anxious, pale-silver-haired adult railway-dispatcher sprite with cap and navy uniform. Her dialogue sits in a caption anchored to her figure and/or in the shared bottom dialogue box. No permanent giant opaque panel hides evidence.

**Primary action:** clicking the line continues, then the player's input box becomes active.

## Screen 4 — Sequential interrogation loop

Finite UI states:

1. `NARRATOR_LINE`: player clicks/taps to continue; chat input disabled.
2. `NPC_LINE`: Lin Wu subtitle; player clicks/taps when ready; historical transcript remains accessible.
3. `PLAYER_INPUT`: player may type any question or click a suggested intent; send initiates a validated turn.
4. `NPC_THINKING`: loading state, cancel option, no duplicate sends; show offline/live status honestly.
5. `NPC_LINE`: show result, then loop to player input on subtitle continuation.
6. `EVIDENCE_INSPECTION`: separate overlay, inspect and annotate; return to whichever dialogue state was active.
7. `DIRECTOR_FEEDBACK`: explicit clue/scene/reasoning outcome from game rules, visually distinct from Lin Wu's speech.

**Suggested questions only after context warrants them:**

- If player inspected clock: “我刚看到时钟停在 00:17。你对列车时间的记忆是什么？”
- If player inspected cloth: “储物柜旁的红色衣料是谁的？”
- If player inspected ticket: “长椅上的车票写着周序，为什么还没有被使用？”
- If player only heard call: “我刚刚听到你结束一通电话。那是谁？”

Do not show “你说谎了” as an objective until the player has obtained an actual conflicting claim and relevant evidence.

## History / evidence sidebar

The left side provides collapsible `现场笔记`, `证据与假设`, `与林雾的对话`, `本局进度` with source and scene provenance. Older lines can be opened without spending case actions. Use a collapsed mode so it doesn't obscure the main cinematic view.

## No-key, model-key, and plot status

- No-key: prewritten NPC dialogue examples; actual game-state consequences still come from local deterministic rules.
- With-key: bounded OpenAI-assisted semantics and dialogue; the model does not validate a collected clue by inventing it.
- Both: explicit status, remaining case actions, and accepted evidence links.
- Six plot actions and the 20-request-per-activation API budget are different counters; avoid implying they are interchangeable.

## End-of-intro acceptance checks

- On first launch, the player can identify the mission without being told the spoiler that 00:12 was fabricated.
- The first full-screen station frame contains **zero visible NPCs** and all intended clue props can be meaningfully zoomed.
- The clock truly reads **00:17** in the rendered clickable close-up, across monitor aspect ratios.
- The ticket close-up actually spells **周序** and is not confused with a real-world transit pass.
- The player can enter NPC conversation even after skipping some observations.
- Entrance and initial dialogue preserve side evidence hotspots and prior observations.
- The same scene remains visually coherent during narration → inspection → NPC dialogue.
- Off-screen phone call and the historical 00:17 call have distinct memory/event IDs.
