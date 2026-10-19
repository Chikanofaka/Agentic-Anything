# Witness Loop · 雨夜回环 — Beta 2 (Ad-Hoc Signed)

**Experimental macOS Apple Silicon (arm64) prerelease. Not Developer ID signed or notarized.**

## Why Beta 2?
Beta 1's archive checksum matched the uploaded release, but the downloaded app failed `codesign --verify --deep --strict` with:

`code has no resources but signature indicates they must be present`

The portable packaging step is updated to apply an **ad-hoc signature to the final assembled .app** (including the edited Info.plist and bundled Python Core) and fail the build unless strict signature verification passes. The release uploader also refuses an app whose code signature fails verification. Beta 1 remains an immutable historical release.

## Install
Download the Beta 2 ZIP, unzip it and move `Witness Loop Portable.app` into Applications. The bundle is ad-hoc signed for integrity, **not notarized or Developer ID signed**, so macOS Gatekeeper may still refuse to launch it. In System Settings → Privacy & Security, a reviewed **Open Anyway** override may be offered on some macOS versions for a trusted download. **Do not globally disable Gatekeeper or delete quarantine attributes as a general workaround.**

## Limitations
Only macOS arm64. Clean-machine Gatekeeper acceptance is not guaranteed. Offline game mode and local save storage are included; optional OpenAI integration remains mock-tested rather than live UAT-certified. The app does not have an auto-updater. No Apple App Store publication.

## Release gate
Strict codesign verification on the built .app is required before uploading the ZIP. This does not prove that macOS Gatekeeper will accept the app when downloaded over Chrome.
