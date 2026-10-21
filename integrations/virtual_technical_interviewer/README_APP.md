# Technical Interview Lab — local macOS App

Build and open from the repository root:

```sh
bash integrations/virtual_technical_interviewer/scripts/build_app.sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

This unsigned development bundle requires macOS 12+, the installed Swift toolchain
to build, and `/usr/bin/python3` to run. It downloads nothing and contains no
network transport. It is a first playable development App, not a portable signed release.

Choose **Guided Onboarding**. Five screens introduce the rules and one fixed
Medium PostgreSQL question. In the room, select Clarification, Plan, SQL, Test
intention or Help; type and record a response. The native bridge sends it to the
existing S02 `InterviewController`. Finish freezes its receipt, performs the
host's handoff-eligibility review, and lets the separate Trainer show a scripted
drill and unfamiliar follow-up. SQL is **NOT_RUN** and both independent assessment
dimensions are **NOT_SCORED**. Feedback is explicitly simulated.

The interface supports English/Chinese, Tab/Enter navigation, Command+Enter to
record, reduced motion, Back, Replay and Skip. Selecting Real AI or Skip opens the
native API Portal immediately. A nonempty credential can only be kept in native
session memory with consent; it remains **activated-unverified**, not authenticated.
Empty credentials are rejected. Disconnect/quit drops the credential reference.
No key enters Python, WebKit, exports or logs. **No paid requests are possible in
this build.** Human live-provider approval remains outstanding.

After choosing to retain a credential in native memory, **Prepare setup —
verification pending** opens an explicitly unverified draft wizard: environment
and duration → question source → Senior Interviewer mechanism → review/preflight.
This preparation path is not native authentication. The provider has not accepted
the credential and the App will not launch a live session from it. No credential
is needed for Guided Onboarding.

Real-interview drafts accept only PostgreSQL/Pandas, 45/60 minutes (derived 3/4
questions), HARD, BYOQ/random generation and the two specified Senior mechanisms.
BYOQ accepts editable JSON or labeled text, up to 4,096 UTF-8 bytes per question.
Required fields are `problem_statement`, `task`, `schema`, `example_input`,
`expected_output`, `environment`, `source`; optional fields are `constraints` and
`source_reference`. Sources are OWNER/LEETCODE/HACKERRANK. Structural review does
not prove correctness, difficulty or fixture validity. Missing/duplicate slots
block progress. Random generation is selectable as a draft; its absent approved
pool blocks launch. No questions are silently supplied.

Both mechanisms compile their allowlisted, versioned source set into separate effective
instructions, with source/policy/configuration digests visible in review.
Human UAT of these engineering policy choices remains pending. Strict help
refusal versus supportive diagnostic questioning is a host-policy fixture test;
it is not evidence of a live model's personality. Preflight always refuses launch
until authentication and independent execution are implemented and validated.

Progress and recorded input are stored privately in
`~/Library/Application Support/Technical Interview Lab/tutorial-v1.json` (0600,
directory 0700). Native restart restores the bounded deterministic command journal
through S02 and verifies its state digest. Tutorial clock samples measure active
process time, not interview performance. Unsubmitted editor drafts are not saved.
These digests detect accidental changes; they are not signatures against a local
file owner. An incompatible/corrupt save is preserved until explicit reset.
Restart/Delete and Replay require native confirmation. Reset deletes the app's
save and crash staging files; it cannot delete exports elsewhere. A save-write
failure preserves current input for rescue export before reset.

Export uses a native Save panel and includes submitted text/code, transcript,
frozen receipt, separate assessment fields and Trainer preview. It is local,
explicit, and contains personal input if you entered it. There is no telemetry.

Verify offline:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --ui --regressions
```

`--ui` opens actual WKWebView windows using isolated synthetic storage, exercises
native keyboard events and the controller, and reopens the App to verify recovery.
It never reads your normal save or enters a real credential. Sanitized logs and
receipts live under `engineering/s03_first_playable/verification/`; generated
bundles and scratch test data remain ignored.

Engineering references: Witness's native worker/navigation/provider boundaries,
the existing S02 controller, and HAL's trusted-host pattern. TIA is **not registered
with the shared Witness interactive HAL registry**; no shared registry authority
was expanded. S03-B configuration, BYOQ and prompt-policy primitives are tested
through the same native/controller wizard as well as unit tests. Real execution,
live AI, calibrated scoring, full Atlas coverage and
the expanded dataset/Pandas product remain future increments.
