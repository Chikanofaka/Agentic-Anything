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

### S03-E1 candidate — 3-question live rehearsal (not timed/scored yet)

A separately gated `Start 3-question AI rehearsal` action becomes available when
three *distinct* BYOQ questions are human-confirmed under the 45-minute
configuration. It allows a genuine Senior Interviewer to handle up to **four
candidate turns per question**, with explicit Finish / Skip actions and three
separately frozen, unscored question records. Source-declared Medium questions
remain Medium and can be used for this *practice* path; formal `setup_launch`
remains blocked and never infers grading from an import.

The current E1 slice is **not yet a timed or graded 45-minute interview**.
E2 will add the host-enforced 45-minute deadline and time ledger; E3 will add
an evidence-based scorecard and Trainer. Automated Mock HTTP coverage is added
under `--ui-rehearsal-test`. On macOS, run the separate increment gate:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E1 --ui --regressions
```

See [`engineering/s03e_three_question/PLAN.md`](engineering/s03e_three_question/PLAN.md)
for gates, constraints and next increments. No real provider UAT or GitHub push
is authorized by this candidate patch.


## S03-E2 — time intelligence (local MVI increment)

In the **three-question AI rehearsal only**, the trusted Python Host records an
independently journalled 45-minute wall-clock deadline and per-question elapsed
times. The clock begins when the first authorized model question is **committed
and presented**, not while the API key is being configured. It includes reading,
writing, dialogue, model wait and subsequent question transitions. A collapsed
clock widget expands to display count-up time, per-question elapsed time, model
wait and the 45-minute limit. WebKit's one-second updates are visual only;
`rehearsal_tick` checkpoints authoritative times locally every 15 seconds and
never makes a provider request. Host commands and native reply commits enforce
the deadline even if WebKit is throttled.

Rehearsal journal entries record replayable host-monotonic + local wall-clock
samples. App downtime counts toward the remaining wall-clock deadline; a
backwards adjustment of more than 2 seconds fails closed as
`CLOCK_INTEGRITY_HOLD`, and expired sessions become `TIMED_OUT` with pending
model replies invalidated. This is a local practice timer, not certified
anti-tamper proctoring; forward clock adjustment or OS modification can make
time expire early. Older E1 saves remain readable but are marked without E2
time evidence rather than backfilled with invented durations.

After every question, the Host records objective candidate message, help, code
submission and clarification counts, with source event IDs. The final export
contains timestamped time events and time metrics. **No code is run or scored**;
Technical/Communication remain `NOT_SCORED` and correctness is `NOT_VERIFIED`.
Full SQL/Pandas execution and evidenced scorecards are later milestones.

Run on macOS:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E2 --ui --regressions
```

The command uses **mock HTTP** and synthetic input; a real paid BYOK UAT
remains a separate, expressly consented Human Gate.

## S03-E2.5A — isolated PostgreSQL fixture grader (standalone engineering increment)

E2.5A is an **opt-in local evaluator**, not yet connected to the three-question
AppKit rehearsal screen. It NEVER uses the current/default PostgreSQL database
or external connection settings: on explicit execution it creates an ephemeral
PostgreSQL 17+ cluster inside a private temporary directory, disables TCP,
accepts requests over a private Unix socket, creates a non-superuser read-only
role, inserts only human-inspected fixture rows, and destroys the cluster after
the attempt. It requires working `initdb`, `pg_ctl`, `psql` server utilities from
`pg_config --bindir` and refuses to start PostgreSQL as root. If the server
executables are missing, it reports `POSTGRES_SERVER_NOT_AVAILABLE` rather than
substituting AI claims for tested answers.

The fixture source MUST be inspected and approved by exact SHA-256 per run.
Its `question_sha256` must be bound to the confirmed BYOQ question before later
Host/UI integration; the bundled synthetic bus example uses a **dummy digest**
and is **NOT** a grading fixture for an actual interview question. Raw LeetCode
examples are **not** automatically approved test cases. This checker reports
`VERIFIED_LOCAL_FIXTURE` for a real PostgreSQL attempt (pass, mismatch, or
query error), never an official LeetCode/HackerRank hidden-test verdict.

From the repository root, inspection makes **zero database calls**:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/run_sql_accuracy.py \
  --fixture integrations/virtual_technical_interviewer/engineering/s03e_postgres_accuracy/examples/bus_demo_fixture.json
```

After human review of the fixture content, copy the printed `sha256` into the
following explicit command (only on a Mac with an isolated server available):

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/run_sql_accuracy.py \
  --fixture integrations/virtual_technical_interviewer/engineering/s03e_postgres_accuracy/examples/bus_demo_fixture.json \
  --sql-file integrations/virtual_technical_interviewer/engineering/s03e_postgres_accuracy/examples/bus_demo_solution.sql \
  --execute --approve-fixture-sha256 "<COPY_INSPECTED_SHA256>"
```

The runner accepts one conservative SELECT/WITH statement (no extra semicolons),
limits output, and compares CSV display values, column names, bag multiplicity
and an explicitly declared ordering policy. It is **not** a general untrusted
SQL isolation service or a type-aware official judge; do not connect this runner
to personal/business databases. Independent per-question Fixture → Code →
Verdict binding, AppKit/WKWebView UX and three-question Scorecard aggregation
remain E2.5B/E3 human-verification gates. Unit tests use no PostgreSQL process:

```sh
python3 -B integrations/virtual_technical_interviewer/run_tests.py
```

### S03-E2.5-B — Native-authorized PostgreSQL accuracy inside the rehearsal

In an active **three-question POSTGRESQL rehearsal**, submit the candidate's
actual code using the **SQL submission** response type. This sends the candidate
message to the approved interviewer model as ordinary conversation, NOT to a
SQL execution or scoring authority. The independent **Local PostgreSQL accuracy
check** then accepts at most 12,000 UTF-8 bytes of an OWNER-reviewed JSON Fixture
using the strict `tia-postgres-fixture/v1` schema. Its `question_sha256` must
match the active question's **confirmed** `content_sha256`, and it is bound to
the current candidate `implement` event and its exact SQL SHA-256. The old
E2.5-A demonstration Fixture's placeholder `aaaaaaaa...` does **not** match a
real imported interview question; it cannot be used to award a grade in the App.

The candidate first clicks **Inspect fixture** (no database call). The Host
validates the fixture, provides a SHA-256 digest and row counts, and saves the
review privately. After inspecting the fixture's actual tables and expected
rows, the user checks the explicit review box and clicks **Approve & run**. A
separate native AppKit confirmation sheet displays the full question, SQL and
Fixture digests before allowing the actual local PostgreSQL process to start.
The WebKit renderer cannot bypass this native confirmation, supply a DB URL,
nominate an executable, forge an execution receipt or claim official hidden
LeetCode scores. The fixture remains private and is never included in the
interviewer prompt or transmitted to OpenAI. Human-reviewed expected answers
ARE visible to the human author; they are not secret judge tests.

One real, isolated PostgreSQL run uses a fresh temporary cluster, a non-TCP
private Unix socket and a low-privilege read-only candidate role (see
`sql_accuracy.py`). `pg_config` is discovered only at a fixed allowlist of
local executable locations (e.g. `/opt/anaconda3/bin/pg_config`), not from
renderer input or arbitrary `PATH`. This is a narrow local practice runner,
**not a certified hostile-SQL sandbox or a signed production release**. The
Mac must have matching PostgreSQL server binaries; otherwise the result is
`NOT_VERIFIED` with a typed error, never a fabricated zero or passing grade.

The Host stores one source-bound result per current question, reports a local
Fixture pass/fail, and freezes it into that question's transcript and export.
After a verified result, duplicate grading is rejected. New SQL written after
inspection invalidates the previous Fixture approval. A saved grading action
replays its recorded backend observation **without running PostgreSQL again**.
SQL execution/wait counts toward the Host's 45-minute limit; any reply arriving
after that deadline is not counted as a valid pass. Legacy S03-E1/E2 saves are
readable; historical evidence is not backfilled. Communication and formal
Technical Capability remain `NOT_SCORED`; official hidden tests remain FALSE.
Pandas, an official hidden-test oracle, numeric interview scorecards and the
Trainer live feedback loop remain separate future increments.

Run the full macOS evidence gate **without a real OpenAI key**:

```sh
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E25B --ui --regressions
```

The new `native-postgres-grading-webkit` test uses a synthetic three-question
rehearsal and MOCK HTTP interview messages, but launches a REAL ephemeral
PostgreSQL instance for one synthetic query. It also exercises native consent,
the question digest, a mismatched fixture rejection, and per-question freezing.
The test's native confirmation click is simulated **only** in isolated
`--ui-grading-test` mode; normal app usage requires human confirmation. This
still needs to be run and verified on macOS before the increment may be
committed/released. Generated verification screenshots, logs, personal
transcripts and local review data should not be automatically published.

## S03-E3A — evidence-based technical scorecard (not an ability grade)

A completed three-question rehearsal displays a read-only **Evidence Scorecard**
from already journalled Host evidence: for each question the current SQL
submission's approved-local-Fixture verification status (if any), candidate
clarification/help/code event counts with evidence IDs, and untrusted local
time. It shows local Fixture coverage, **not a success percentage for the full
problem**. If SQL was modified after a passed local test, only the earlier
version is known to have passed; the latest implementation is `NOT_VERIFIED`.

The scorecard is also included in the explicit local export. Reopening old
sessions does not run PostgreSQL or change saved replay digests. Technical,
Communication, Overall and formal exam status remain `NOT_SCORED`/blocked.
This is not a Trainer evaluation, official hidden test, or proctored exam.

Mac automated verification (mock model HTTP; live ephemeral local Postgres):

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3A --ui --regressions
```

See `engineering/s03e_evidence_scorecard/README_E3A.md` for evidence-policy
boundaries and final Human Gate. Generated `verification_E3A` is not intended
for public commit until reviewed for private information.


## S03-E3B — Communication Evidence Rubric (candidate-source projection)

E3B adds the six PRD v3 Communication dimensions C01–C06 and an explicit
communication strategy checklist in the live three-question rehearsal. This is
a deterministic, read-only communication *evidence map*, not an automatic
communication performance rating. Candidate Event IDs, SHA-256 fingerprints,
short source excerpts, and interviewer-reply → candidate-action sequences are
shown only as potential evidence for subsequent contextual review. A help
request, plan statement, or follow-up is **not** automatically a good request,
a good plan, or proof of learned feedback. Professional closure (C06) is
`NOT_OBSERVED` until a real closing-statement event exists.

PRD's 60 Technical / 40 Communication baseline is a **hypothesis**, and proposed
C01–C06 weights (6/7/7/9/7/4) and anchors are uncalibrated. E3B assigns no
0–4 anchors, no numeric points, no mental-impression bonus and no hiring grade.
The distinct read-only `communication_evidence` is returned by Host snapshot
and export; it does not alter existing E3A scorecards, prior receipts, or save
digests. Recovery never contacts an LLM or PostgreSQL for communication review.
`validate_review_proposal` is a fail-closed future rater-draft contract; even
a valid proposal stays `PENDING_HUMAN_REVIEW` and cannot grant scores.

Mac gate (mock provider + real local approved PostgreSQL only):

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3B --ui --regressions
```

See `engineering/s03e_communication_rubric/README_E3B.md`.

## S03-E3C-A — Grounded Trainer Lab (offline; model request NOT implemented)

After the 3-question interview is locked, the completion view includes an
**offline Trainer Lab** that proposes prioritized, measurable practice based on
source-bound E3A correctness and E3B communication observations. It lists exact
candidate Event IDs, question/fixture fingerprints when available, and fresh
independent retest conditions. A local PASS never means full skill mastery, a
missing C01–C06 event never means low competence, and all proficiency grades
remain `NOT_SCORED`. Both Host snapshot and explicit export include the
`grounded_trainer` view, and reopening the same save regenerates the same view
without paying for a model call or rerunning SQL. This changes no stored event
or historical receipt digest.

E3C-A supplies a strict **future model proposal** validation boundary but does
NOT invoke a real AI Trainer, does not generate personalized AI prose and does
not implement SMART reminders. The next E3C-B increment must separately wire
native BYOK paid consent, safe transcript disclosure and model response review.

Mac gate (mock OpenAI/real synthetic local PostgreSQL, zero real provider calls):

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3C --ui --regressions
```

See `engineering/s03e_grounded_trainer/README_E3C_A.md` for limitations and
test/release boundaries. Local `verification_E3C` is not part of public code.

### S03-E3C-B: Native BYOK AI Trainer · evidence-grounded model proposal

- After closing the three-question interview, **Native BYOK · AI Trainer proposal** is optional. E3-C-A offline drills remain available and do not require a key.
- Open the native API Portal (session-only OpenAI credential, model, bounded 1–20 request cap, paid-request consent). Every subsequent Trainer request requires its **own macOS native confirmation**. The confirmation displays the selected frozen Trainer digest and citation policy, and states that cancelled/rejected requests may still be billed.
- The native worker constructs a single selected source-bound drill, required `event_id` citations, `question_sha256`/`fixture_sha256` and **up to 280 Unicode characters from each cited candidate event**. Short submitted SQL snippets can be included **in full**. The request does **not** include the full transcript, complete local fixture tables, unrelated questions or credentials in model-visible content.
- The native `TIAOpenAIAdapter` uses the existing fixed HTTPS `/v1/responses` endpoint, `store=false`, no provider tools, no redirects, max 600 output tokens, one request at a time and strict JSON reply envelope. The server returns a **JSON object serialized inside the `reply` string**; a malformed/overlong response is rejected without an automatic retry.
- The Python Host independently validates the exact prepared `transaction_id`, generation, frozen `trainer_sha256`, exact model-input digest, selected drill, precise candidate Event IDs, fixture digest and proposal schema. It records a bounded, locally private `PENDING_HUMAN_REVIEW` proposal **without numeric capability, communication or hiring grade**. Cited IDs and hashes are evidence references, *not* a guarantee of semantic truth. Output must be checked by a human before use.
- A completed paid proposal is replayed from the local journal without another provider call. An interrupted in-flight request is cancelled on startup and explicitly labelled uncertain; a charge may have occurred and **retry is never automatic**. A subsequent user-initiated request requires a new native consent.
- Existing E1–E3CA journal digests and original saved interview/SQL receipts remain unchanged. `native_trainer_feedback` is an additional read-only export projection. Do not confuse the separate offline `grounded_trainer.paid_provider_requests=0` with native usage counters, which are measured only for the current app process.
- Automated verification (`--increment S03-E3CB --ui --regressions`) uses closed `TIATestHTTPProtocol` mock networking and a real isolated local PostgreSQL fixture. Real paid OpenAI UAT, semantic assessment and human release approval are **not** implied by automated success.

### S03-E3D: evidence-linked SMART improvement sprint (pending macOS acceptance)

After a three-question rehearsal is locked, the App derives a deterministic seven-day SMART plan from the first three E3-C-A evidence-grounded drills. The user explicitly clicks **Start** to create a Host-owned time origin and 1/3/7-day checkpoints. Practice and claimed external retests are appended to the private journal and survive restart. Every record remains `SELF_REPORTED_UNVERIFIED`; even a 64-digit external artifact digest does not establish that PostgreSQL was executed or that ability improved. The frozen technical/communication results and previous real OpenAI Trainer proposal are read-only and never rescored. Separate macOS regression: `verify_app.py --increment S03-E3D --ui --regressions`. Scope, evidence contract and unresolved verification gates: `engineering/s03e_smart_plan/README_E3D.md`.


Independent Evaluator MVF: [operation, policy, verification and UAT](engineering/evaluator_agent/README.md). The owner-confirmed PRD v3 11-criterion proposal is the operating evaluator; 12-metric experiments remain separate.
