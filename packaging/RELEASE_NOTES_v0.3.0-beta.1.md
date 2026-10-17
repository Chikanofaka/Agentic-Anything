# Witness Loop · 雨夜回环 — v0.3.0 Beta 1

**Mac-only prerelease for Apple Silicon (arm64), macOS 12 or later (broader OS compatibility not certified).**

The first downloadable build of Witness Loop: explore a rain-soaked station, inspect four objects, meet the anxious dispatcher Lin Wu, review evidence and reach one of three bounded case outcomes. Native AppKit/WebKit UI, deterministic HAL Core, bilingual experience, session saves and the Lin Wu icon are packaged together.

## Installation

1. Download the DMG from this Release (only after it has been Developer ID signed and Apple notarized).
2. Open the DMG, drag **Witness Loop.app** to **Applications**, then launch from Applications.
3. Play offline with simulated dialogue. Optional OpenAI-enhanced dialogue requires a separate OpenAI Platform API key entered only in the native secure sheet, with explicit consent and usage limits. This feature has not yet passed a live paid-model UAT.

## Limitations

- This beta is for Apple Silicon Macs. Intel and universal builds are not included.
- The model provider adapter has automated mocked tests; real-model dialogue quality has not been certified.
- Player saves are stored in `~/Library/Application Support/Witness Loop/` and are not cloud-synced.
- No in-app updater. Download newer releases manually.
- Distribution rights, third-party references, art assets and privacy disclosure must be approved by the publisher before public release.

Source documentation: [Repository README](https://github.com/Chikanofaka/HAL-P2D-001) · [Native host boundaries](https://github.com/Chikanofaka/HAL-P2D-001/blob/main/integrations/witness_loop/native/README.md)
