# Witness Loop · 雨夜回环 — v0.3.0 Beta 1 (UNSIGNED)

**Experimental GitHub prerelease — macOS Apple Silicon (arm64) only.** This archive contains an unsigned and unnotarized macOS app. It has **not** passed the Apple Gatekeeper/Developer ID distribution process or external-Mac compatibility testing. Install only if you trust the publisher and understand this limitation.

## Install
1. Download `WitnessLoop-v0.3.0-beta.1-unsigned-macOS-arm64.zip` and its SHA-256 checksum from this release.
2. Extract the archive, then move `Witness Loop.app` to Applications.
3. Because the application is not signed/notarized by an identified Apple Developer, macOS may block its first launch. If you trust this specific release, try opening it from Finder; where macOS offers an override, review it in **System Settings → Privacy & Security → Open Anyway**. Availability and wording depend on macOS. Do not disable Gatekeeper globally or run `xattr -dr com.apple.quarantine` as general installation advice.
4. Launch **Witness Loop** and play offline. Optional live AI dialogue requires a separate OpenAI Platform API key and consent in the native secure window. This feature has not completed paid live-model UAT.

## What's included
- Rainy railway station and original Lin Wu character-IP icon
- English / Mandarin playable local detective case, four inspectable props and three bounded outcomes
- Deterministic HAL Core, bundled Python worker and persisted local saves

## Known limits
- Unsigned / unnotarized: no official Apple security assessment; player installation may be blocked.
- Apple Silicon only; Intel and macOS compatibility outside the original host are unverified.
- Player saves: `~/Library/Application Support/Witness Loop/`. Do not send private saves or API keys in issue reports.
- Offline dialogue is simulated. Model-provider adapter is mock-tested, not certified for live quality.
- No automatic update mechanism, warranty or App Store availability.
- Artwork and redistribution terms require publisher approval; no assumption that a public repo grants reuse rights.

Development branch: [feat/wtl029-portable-beta](https://github.com/Chikanofaka/HAL-P2D-001/tree/feat/wtl029-portable-beta).
