# WTL-029 — Standalone macOS Beta Build (unsigned engineering preview)

**Release status (2026-10-17):** [Unsigned macOS Apple Silicon Beta 1 is published](https://github.com/Chikanofaka/HAL-P2D-001/releases/tag/v0.3.0-beta.1-unsigned). The build bundles Python HAL into `Contents/Helpers/WitnessCore/` and disables the developer-mode fallback to `/usr/bin/python3`. Player saves live in `~/Library/Application Support/Witness Loop/`. **Only the experimental, unsigned ZIP has shipped.** Developer ID signing, Apple notarization, clean second-Mac validation, and live AI personality UAT remain pending.

## Prerequisites

On a Mac with the existing Swift compiler, run:

```bash
cd ~/Desktop/HAL-P2D-001
git fetch origin
git switch feat/wtl029-portable-beta
git pull --ff-only origin feat/wtl029-portable-beta
```

The packaging Python **must be Python 3.9+ with a compatible PyInstaller version**. Prefer an available Python 3.12 installation. System `/usr/bin/python3` is still used for **source compilation/build/test on the developer Mac**, but the resulting release-mode bundle must not use it at runtime.

To prepare a deliberately isolated packaging venv (one-time installation):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'pyinstaller>=6,<7'
```

Review dependency licensing and the packaging Python's target macOS architecture before distribution. Never commit the venv, generated binary, saves or API credentials.

## Build and offline test

Quit the old app, then:

```bash
WITNESS_PACKAGING_PYTHON="$PWD/.venv/bin/python" bash scripts/build_witness_portable_beta.sh
```

This script deliberately builds **two** apps: the existing local developer app and a new separate `integrations/witness_loop/dist/Witness Loop Portable.app`. It refuses to overwrite the latter. It checks the packaged HAL Core using a synthetic isolated save and one `snapshot` request. It does not contact the OpenAI API.

**Important:** each rerun needs explicit disposal/archiving of the *previous generated preview* only:

```bash
mv "integrations/witness_loop/dist/Witness Loop Portable.app" \
   "integrations/witness_loop/dist/Witness Loop Portable.previous.app"
```

Remove or rename that previous preview intentionally before another run; the script does not delete artifacts automatically.

## Relocation and native UI test (no credentials)

After the build passes, copy the standalone preview to a location **outside** the Git checkout, then exercise the actual UI smoke suite:

```bash
mkdir -p "$HOME/Desktop/WitnessStandaloneQA"
ditto "integrations/witness_loop/dist/Witness Loop Portable.app" \
      "$HOME/Desktop/WitnessStandaloneQA/Witness Loop Portable.app"
"$HOME/Desktop/WitnessStandaloneQA/Witness Loop Portable.app/Contents/MacOS/WitnessLoop" --ui-self-test
```

`--ui-self-test` uses temporary synthetic saves and disables live provider use. It should report **21 checks passed** without any credentials. Confirm that `Contents/Info.plist` has `WitnessDevelopmentBuild=false`, the icon exists, and the new app still opens from the relocated directory; the development repository may stay present during this first smoke test, so this does not *by itself* prove true independence.

A **clean second Mac** (matching CPU architecture, supported macOS) without the project checkout or developer Python is the next acceptance gate. A successful test on the developer's Mac is necessary but not sufficient.

## Remaining limitations and future signed release gates

- **Unsigned and not notarized:** the experimental ZIP is publicly available, but remains untrusted by Apple Gatekeeper. Developer ID signing and notarization remain prerequisites for the planned signed distribution route; the unsigned beta is not an Apple-certified build.
- **CPU architecture:** PyInstaller builds for its current Python/host architecture. Universal binary support is not established.
- **Privacy and rights:** confirm code/asset redistribution rights, privacy notice, API-key disclosure, and artifact license before a binary release.
- **macOS App Store:** requires its own sandbox/signing/entitlement and review work. A GitHub Developer ID build does not automatically become an App Store package.
- **AI claims:** the OpenAI adapter remains mock-tested only for the current release candidate until a separately authorized live test.
