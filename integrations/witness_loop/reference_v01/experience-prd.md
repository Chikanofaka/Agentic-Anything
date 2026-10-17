# WTL-029 Experience-Refined PRD

## User / Need / JTBD

面向喜欢 mystery、RPG 与 immersive-sim 的玩家。固定对话树限制表达，而普通 AI chat 即使流畅也没有可复核的游戏后果。玩家要用自己的话取证，并看到角色记忆、关系、证据和结局真的改变。

## Product thesis

语义自由只有进入目标、规则、持久状态、反馈和结局，才是 AI-native gameplay。Witness Loop 用角色 identity + structured memory + relationship variables + bounded state machine + deterministic ending evaluator 把开放对话变成游戏机制。

## Wedge / Non-goals

一个证人、一个失踪案、三场景、六回合、四条证据、三种结局。非目标：开放世界、多角色实时模型、语音、多玩家、生产审核。

## Direct-product fidelity

PASS。自由提问、角色约束、记忆写入、跨场景召回、证据解锁、矛盾与结局全部是未来游戏核心；移除解释文字后仍可玩。工程化将沿用这些状态接口。

## Three-layer view

`Input/Data（玩家原话、identity、evidence） → Logic/AI（意图分类/生成、memory gate、state/ending evaluator） → Game Experience（visual novel、evidence board、HUD、verdict）`

## Magic moment

玩家承诺保护林雾；第二场景她引用玩家称呼与承诺，释放 00:17 通话。召回不是装饰台词，而是证据与真相结局的必要条件。

## UAT / Falsifier

5 名玩家中至少 3 名必须注意到跨场景记忆、认为讯问本身值得继续、能区分真实状态与模拟语言。否则 MODIFY：降低自由文本权重或加强证据 adjudication；若玩家只把它当聊天框则 BLOCKED。

## Smallest post-DOING boundary

Server-side 可插拔模型、JSON schema、memory admission、成本上限、提示注入防护、golden replay；保持 1 case/1 witness，不扩内容规模。
