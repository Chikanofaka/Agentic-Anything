# 雨夜回环 · Witness Loop

### AFTER THE LAST TRAIN

*末班车驶离之后，有人失踪。有人沉默。真相还在雨中。*

<p align="center"><img src="../integrations/witness_loop/ui/assets/linwu_anxious.png" width="260" alt="Lin Wu, the dispatcher." /></p>

Witness Loop is **the first public Type B harness application experiment** in the [Harness Activation Layer research project](../README.md). It explores how a deterministic investigation game could provide a bounded place for intelligence-driven NPC conversation and potentially richer social interactions. It does **not** yet contain autonomous multi-agent characters or validated production-quality LLM-driven gameplay.

![The rainy Yunjiang railway station](../integrations/witness_loop/ui/assets/platform_empty.png)

**[Download the playable Mac preview](https://github.com/Chikanofaka/HAL-P2D-001/releases/tag/v0.3.0-beta.3-adhoc)** (Apple Silicon)

## 最终安装流程

![下载 → Applications → 安全授权 → 进入云江站](../branding/after-the-last-train-install.svg)

1. 从 GitHub 下载 ZIP 并解压游戏。
2. 在 Finder 中把 `Witness Loop.app` 移到 **Applications**，然后再首次打开。
3. 如果你信任此下载，而 macOS 阻止启动，请按需使用 **System Settings → Privacy & Security → Open Anyway**。
4. 从 Applications 启动游戏，进入云江站展开调查。

One Chrome-downloaded installation was reported to load successfully after the Finder move and macOS approval. This Mac preview is **ad-hoc signed but not Apple Developer ID signed or notarized**. Do not disable Gatekeeper. Other machines, full human playthrough and live-model UAT remain pending.

## A testable idea, not an unlimited AI world

The scripted offline investigation and persistent case state are real. HAL controls what the player can inspect, which evidence counts, and which verdict can follow. An optional OpenAI API adapter is available as an experimental feature, but real-model personality acceptance has not been completed.

This is a visual-novel / mystery-game MVP and a stepping stone toward exploring more independent NPC behavior, agent memory, adaptive relationships and human-agent social play—**future experiments**, not shipped features.

## Behind the scenes

[Type B implementation PRD](../engineering/HAL_WITNESS_TYPE_B_PRD.md) · [Implementation evidence](../engineering/WITNESS_INTEGRATION_RECEIPT.md) · [Detailed game engineering guide](../engineering/WITNESS_TECHNICAL_SHOWCASE.md) · [Art provenance](../integrations/witness_loop/ASSET_PROVENANCE.md)
