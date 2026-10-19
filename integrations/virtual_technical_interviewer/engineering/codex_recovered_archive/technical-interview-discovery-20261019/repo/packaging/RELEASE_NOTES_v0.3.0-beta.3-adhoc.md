# 雨夜回环 · Witness Loop

### AFTER THE LAST TRAIN

*末班车驶离之后，有人失踪。有人沉默。真相还在雨中。*

**[下载 Mac 游戏 · Download for Apple Silicon](https://github.com/Chikanofaka/HAL-P2D-001/releases/download/v0.3.0-beta.3-adhoc/WitnessLoop-v0.3.0-beta.3-adhoc-macOS-arm64.zip)**

## 最终安装流程

![安装步骤：下载、移入应用程序、安全授权、进入云江站](https://raw.githubusercontent.com/Chikanofaka/HAL-P2D-001/main/branding/after-the-last-train-install.svg)

1. **下载游戏** — 从 GitHub 下载 ZIP 并解压 `Witness Loop.app`。
2. **移入应用程序** — **先用 Finder** 把游戏移到 **Applications**，再尝试启动。不要直接从 Downloads 打开。
3. **安全授权** — 仅在你信任此下载的情况下，如果 macOS 阻止启动，请到 **System Settings → Privacy & Security → Open Anyway** 并按提示确认。
4. **进入云江站** — 从 Applications 打开游戏，寻找停在 **00:17** 的时钟，展开调查。

This Mac preview is **ad-hoc signed but not Apple Developer ID signed or notarized**. Apple Silicon only. The downloaded app's first launch was confirmed on one Mac after moving it into Applications with Finder and completing manual macOS security approval. Full human playthrough and broad compatibility are pending. Do not disable Gatekeeper or remove quarantine attributes.

### 故事简介 · The mystery

A traveler has vanished after the last train. Meet **林雾 · Lin Wu**, investigate four clues, and decide which story the evidence supports. Offline mode runs locally without a key; optional live-model dialogue is experimental and needs separate API billing.

<details>
<summary>Technical build identity, changes and limitations</summary>

**Build identifier:** `v0.3.0-beta.3-adhoc` (historical asset filename retained for stable downloads).

**What changed:** Beta 1 had a broken app signature. Beta 2 corrected the signature but the user reported a blank window when the quarantined app was opened from Downloads. Beta 3 added WebKit error diagnostics, UI readiness synchronization and validated the staged and ZIP-extracted candidates with **21/21 native UI checks each**. The downloaded Beta 3 app initially hit a 12-second timeout under confirmed macOS App Translocation. Moving it to Applications using Finder resolved the loading issue on that Mac.

**Limitations:** No Developer ID, Apple notarization, App Store distribution, automatic updates, or broad macOS/Intel verification. The optional OpenAI mode is mock-tested, not live-persona human-certified. Saves are local to `~/Library/Application Support/Witness Loop/`. Distribution rights of source, artwork and bundled Python/Anaconda components remain subject to publisher review.

**Developer references:** [Technical guide](https://github.com/Chikanofaka/HAL-P2D-001/blob/main/engineering/WITNESS_TECHNICAL_SHOWCASE.md) · [Issue history](https://github.com/Chikanofaka/HAL-P2D-001/issues/4)

</details>
