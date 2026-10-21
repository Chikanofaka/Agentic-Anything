# Technical Interview Lab — local macOS App

From the repository root:

```sh
bash integrations/virtual_technical_interviewer/scripts/build_app.sh
open "integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app"
```

This unsigned development App requires macOS 12+, the installed Swift toolchain
to build, and `/usr/bin/python3` to run. It downloads no dependencies. It is not a
portable signed release.

**Guided Onboarding** remains completely offline. Its five screens use one fixed
Medium PostgreSQL question and the original S02 controller. Submitted text is
recorded, feedback is **SIMULATED**, SQL is **NOT_RUN**, and Technical Capability
and Communication remain separately **NOT_SCORED**. Host closure freezes the
receipt before the separate Trainer receives its permitted scripted review.

**Real AI Interview** immediately opens the native API Portal. Cancel it and use
**Preview interview configuration** to explore the entire Wizard without a key
or paid request. The exact 16 configurations remain PostgreSQL/Pandas, 45/60
minutes with derived 3/4 Hard questions, BYOQ/random source, and Strict/Supportive.
BYOQ accepts pasted LeetCode/HackerRank natural-format questions (plus legacy
JSON/labeled fields). S03-D accepts up to 8,192 UTF-8 bytes per question,
imported one slot at a time under the existing 32KB Worker request limit.
The candidate selects a source, clicks **Extract question**, edits detected
fields (especially Schema and Example Output), and explicitly confirms.
Original text and review stay in the private App save. Structural extraction
never authorizes execution or grading. Image-only HackerRank schemas are
flagged `IMAGE_SCHEMA_NOT_IMPORTED`; the current version requires manual schema
entry and does not claim screenshot decoding. The absent validated pool and
execution adapters continue to block full interview launch.

**S03-D single-question BYOQ rehearsal:** after confirming the extracted fields,
select **Practise this question with Live AI (unscored)**. This binds the actual
confirmed task, schema and examples to the existing native OpenAI model request,
then opens the API Portal for explicitly authorized, bounded paid usage. The
45→3/60→4 Hard formal examination policy remains unchanged. An imported Medium
problem may be used for practice but is not approved as a Hard exam item.
Live rehearsal has no SQL/Pandas execution or numerical grades, and still limits
the candidate to a single submitted turn. The original built-in preview
continues to work without an imported question.

S03-C adds **Live Conversational Preview**. In the native sheet choose a model
(default `gpt-4.1-mini`), a cap of 1/2/5/10/20 requests, and explicitly consent to
paid usage. Activation stores the key only in native process memory and makes
**zero requests**: status is `activated-unverified`. **Verify access & open
preview** uses one authorized request. Only a successful, schema-valid response
can produce `live-verified`. Then one candidate turn, at most 4,096 UTF-8 bytes,
can receive a model-backed Senior Interviewer reply. Each explicit retry uses an
additional request; it preserves the same already-recorded candidate evidence.
Close the preview to freeze and review its receipt. This is an **unscored
conversation**, not a full technical interview or SQL correctness test.

Select Strict or Supportive through the configuration Wizard before verifying.
Both compile the existing verified identity, soul, AGENTS and skills sources;
effective instruction and policy hashes accompany each committed response.
Strict help requests authorize a refusal; Supportive authorizes a diagnostic
question without a solution. Unclear requirements follow corrected B05
clarification/reassessment. These are engineering policies pending human UAT;
60/40 remains provisional and no numerical score is assigned. The host protects
authority and reference access; prompt compliance in natural language still
requires live UAT. Live Trainer calls are not enabled in this slice.

Swift alone sends HTTPS to `https://api.openai.com/v1/responses`, using ephemeral
URLSession, no redirects/retries, 30-second timeout, 600 output-token maximum,
bounded bodies, strict JSON and a native request cap. The cap is not a currency
budget. Actual token usage is shown only when supplied; missing/error/cancelled
usage remains unknown. Totals cover measured responses in the current App
process; per-activation and process-lifetime attempts are tracked separately.
No real key enters Python, WebKit, subprocess arguments, saved data, exports or
logs. Disconnect/quit clears the native credential reference. Provider retention
policies still apply even with `store:false`.

The Python Worker prepares approved prompts, Swift performs the asynchronous
request, and Python validates/commits a bounded reply. Native-only IPC commands
are not WebKit bridge actions. Request IDs, activation generations, session phase
and event revision reject stale, duplicate or closed-session replies. Cancel or
disconnect before commitment invalidates the pending response; an already-sent
request may still be billed. Once native has submitted an atomic controller
commit, cancellation cannot undo that saved turn; the App reports this boundary.
Model text cannot issue commands, authorize hints, execute code or assign scores.

Progress is saved privately at
`~/Library/Application Support/Technical Interview Lab/tutorial-v1.json` (0600,
directory 0700). It includes submitted tutorial/preview text and model replies.
Reopening replays a bounded command journal without network calls, invalidates
unfinished native transactions and starts provider status offline. Previous
offline receipts stay compatible. Up to eight closed previews can be archived
before reset. An incompatible/corrupt save is preserved until explicit reset;
save errors permit rescue export. Digests detect accidental changes and are not
signatures against a local file owner. Unsubmitted editor drafts are not saved.

Restart/Delete requires native confirmation and deletes the App save and crash
staging files, including preview history. It does not delete previously exported
files. Export uses a native Save panel, includes personal submitted text and
frozen evidence, and does not transmit it. Failed-request totals cannot be
reconstructed after restart; committed reply usage remains in the transcript.
There is no telemetry. English/Chinese, keyboard controls and reduced motion are
supported.

Run all automated verification, with **mocked HTTP only**:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-C --ui --regressions
```

The UI tests open actual native windows and use isolated synthetic storage.
Allow them to operate their own credential sheets; never enter a real key in a
test window. Every automated App mode installs a fail-closed URLProtocol mock.
Receipts are in `engineering/s03c_live_byok/verification/`. Generated bundles and
scratch data stay ignored. Historical S03-A/B receipts are preserved.

[S03-C handoff and separately authorized live UAT](engineering/s03c_live_byok/HANDOFF.md)
document measured verification and remaining gates. No paid live test has been
performed by this implementation task. TIA has not been registered with the
shared Witness HAL interactive registry; no shared authority was expanded.

### S03-D Patch candidate verification

Run from repository root with no real API key:

```sh
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --ui --regressions
```

The new Python tests verify source-shaped raw import, per-slot bounds, human
confirmation, immutable live question binding, journal restart and the formal
launch gate. Native/WebKit tests require macOS; their tests use synthetic data
and mock HTTP. Only after both test suites pass should the S03-D branch enter
human UAT, followed by an explicit approval to merge/push. No live requests
are made by automated tests. Image upload, SQL execution, grading, multimodal
vision and multi-turn voice remain separate later milestones.
