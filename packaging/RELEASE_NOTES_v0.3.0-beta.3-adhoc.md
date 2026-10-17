# Witness Loop · 雨夜回环 — v0.3.0 Beta 3 (Ad-Hoc Signed)

**Experimental macOS Apple Silicon (arm64) GitHub prerelease. Ad-hoc signed only; NOT Developer ID signed, notarized, or distributed through the App Store.**

## What's fixed since Beta 2
Beta 2 could be opened after the macOS Privacy & Security override but displayed an entirely white game window. All four core UI assets were confirmed present in the downloaded bundle. Beta 3 integrates targeted WebKit navigation/load failure reporting, JavaScript/CSS/DOM readiness checks, and a first-snapshot synchronization fix to avoid UI initialization races with the bundled Python HAL Core.

The **local isolated release candidate** passed 21/21 native WebKit UI integration checks (case brief, station, evidence inspection, Lin Wu, free/offline dialogue, saved state, and all three verdict outcomes) without real model requests or credentials. Its ad-hoc app signature also verified before and after the GUI check.

Beta 3's publication script independently checks the final zipped and extracted app, including a native UI smoke run on the extracted candidate. **Post-release confirmation (2026-10-17):** A user downloaded Beta 3 with Chrome. Opening from Downloads translocated the app and led to the 12-second game-screen timeout. Moving the app to /Applications using Finder and using macOS Privacy & Security → Open Anyway resolved the loading issue. Initial downloaded-app startup is confirmed; an entire gameplay session is not yet confirmed. A successful packaging gate is not equivalent to that final user acceptance.

## Download & opening
Download `WitnessLoop-v0.3.0-beta.3-adhoc-macOS-arm64.zip`, optionally verify the accompanying SHA-256 checksum, then extract `Witness Loop.app` and **move it into /Applications using Finder before launch** (opening from Downloads can cause App Translocation and a white-screen timeout). Because this build has no Apple Developer ID signature or notarization, macOS may block its first launch. Only if you trust this exact download, use the system-provided **System Settings → Privacy & Security → Open Anyway** override if offered; macOS may require an administrator's approval. **Do not disable Gatekeeper globally or use indiscriminate quarantine removal.**

## Limitations
- Apple Silicon only; Intel Macs and other macOS versions not broadly validated.
- Offline scripted dialogue and deterministic HAL case outcomes are included. Live OpenAI requests are optional and not certified by paid-model human UAT.
- Existing local player data under `~/Library/Application Support/Witness Loop/` is not deleted by this installer.
- No automatic update, Developer ID notarization or App Store version.
- Beta 1 has a known invalid signature. Beta 2 has a reported blank-screen issue and remains a historical prerelease.
- Distribution rights for packaged code/artwork and the Python/Anaconda-linked dependencies remain subject to the publisher's review.

## Acceptance state
**Candidate UI integration: PASS (21/21 × 2). Downloaded startup: PASS after Finder move to /Applications and Gatekeeper manual approval. Complete downloaded-game playthrough: PENDING.** Report blank screens and launch errors via [issue #4](https://github.com/Chikanofaka/HAL-P2D-001/issues/4).
