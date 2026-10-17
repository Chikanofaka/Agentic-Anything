# 雨夜回环 · Witness Loop

<p align="center">
  <img src="integrations/witness_loop/ui/assets/linwu_anxious.png" width="235" alt="Lin Wu — the mysterious railway dispatcher." />
</p>

<p align="center">
  <strong>AFTER THE LAST TRAIN</strong><br/>
  <em>At 00:17, the clock stopped. Someone disappeared. Someone remembers.</em><br/>
  <em>末班车驶离之后，有人失踪。有人沉默。真相还在雨中。</em>
</p>

<p align="center">
  <a href="#begin-your-investigation">Begin your investigation</a> ·
  <a href="#your-first-four-steps">Install on Mac</a> ·
  <a href="#inside-the-mystery">The story</a> ·
  <a href="#for-the-curious">Behind the scenes</a>
</p>

<p align="center">
  <img src="integrations/witness_loop/ui/assets/platform_empty.png" width="950" alt="An empty station in the rain, after the last train." />
</p>

> **A playable detective-story preview for Apple Silicon Macs.** Your decisions and evidence matter. Start entirely offline, without an account or API key. The optional AI conversation mode is experimental, and the game is **not Apple notarized**.

## Begin your investigation

**[Download the game for Mac →](https://github.com/Chikanofaka/HAL-P2D-001/releases/download/v0.3.0-beta.3-adhoc/WitnessLoop-v0.3.0-beta.3-adhoc-macOS-arm64.zip)**

[Other release files & SHA-256 checksum](https://github.com/Chikanofaka/HAL-P2D-001/releases/tag/v0.3.0-beta.3-adhoc) · macOS with Apple Silicon (M-series) · Experimental preview · No paid Apple Developer verification

## Your first four steps

![Illustrated four-step macOS game onboarding: download, move to Applications, Open Anyway, enter the mystery.](branding/after-the-last-train-install.svg)

**1. Accept the invitation.** Download the Mac ZIP above and double-click it to extract **Witness Loop.app**.

**2. Bring the game home.** In **Finder**, move the extracted app into **Applications** **before opening it**. On a real Chrome download, launching from Downloads caused macOS App Translocation and a blank game window; moving it to Applications resolved that loading issue.

**3. Cross the gate—only if you trust the download.** Because this is an experimental, **ad-hoc-signed and unnotarized** preview, macOS can block the first launch. If you recognize the source and want to proceed, open **System Settings → Privacy & Security → Open Anyway** (if offered) and approve as prompted. You may need administrator authorization. **Do not disable Gatekeeper globally or remove quarantine attributes as a shortcut.**

**4. Step into the rain.** Open **Witness Loop** from Applications. Read the case brief, enter the station and begin inspecting the clues.

One actual Chrome-downloaded installation has been confirmed to load correctly after the Finder move and macOS approval. Full end-to-end player acceptance on that downloaded installation, Intel compatibility, and wider macOS testing are **not yet verified**.

## Inside the mystery

A missing traveler. A station clock frozen at **00:17**. A discarded ticket. A trace of red fabric. One nervous dispatcher—**Lin Wu**—who may know more than she admits.

Walk the deserted platform, look closely at four clues, question Lin Wu in English or Mandarin, and decide what truly happened. Your choices can lead to **three different conclusions**.

**How to begin playing:** Read the opening → enter the station → click the four objects to examine evidence → approach Lin Wu → ask questions → examine your notebook → make a judgment.

The **offline** mode uses scripted character responses and a persistent local case state; no account, model call or payment is required. An **optional** experimental OpenAI-enhanced mode uses an independently billed OpenAI Platform API key entered only in the app's native secure form. Its conversational quality has not completed real-model human acceptance.

## A note from the creators

This is a small, public, experimental game—not a certified App Store title. Its original artwork, investigation structure and playable Mac experience are the focus here. The story and game may evolve; saves are stored locally.

If anything does not load, first confirm the app was **moved with Finder into Applications**. For a reproducible bug or gameplay issue, [tell us what happened](https://github.com/Chikanofaka/HAL-P2D-001/issues).

## For the curious

The playable world is built with Swift, WebKit, Python and a deterministic case engine. The model may propose dialogue, but it cannot rewrite canonical evidence or decide a verdict. The codebase began as an engineering study; technical names are preserved for maintainers, not required knowledge for players.

- [Complete technical showcase and original engineering evidence](engineering/WITNESS_TECHNICAL_SHOWCASE.md)
- [Character and art provenance](integrations/witness_loop/ASSET_PROVENANCE.md)
- [Source provenance](integrations/witness_loop/SOURCE_PROVENANCE.md)
- [Game guide](integrations/witness_loop/README.md)
- [Release notes and technical limitations](packaging/RELEASE_NOTES_v0.3.0-beta.3-adhoc.md)

**Development status:** Public experimental download and first launch confirmed on one Mac; automated native UI integration passed **21/21 checks** on both staged and ZIP-extracted candidates. Full downloaded-app playthrough, real-model persona testing, Apple notarization, and broad compatibility remain future work.

<sub>Development repository: Chikanofaka/HAL-P2D-001. Historical technical release tag: v0.3.0-beta.3-adhoc. Keeping these identifiers stable preserves existing links and verifiable build provenance.</sub>
