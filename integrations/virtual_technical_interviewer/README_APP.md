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
separately. Real execution, live AI, calibrated scoring, full Atlas coverage and
the expanded dataset/Pandas product remain future increments.
