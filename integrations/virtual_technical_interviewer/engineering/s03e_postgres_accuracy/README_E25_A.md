# TIA S03-E2.5A — Local PostgreSQL Accuracy Engine

## Boundary

This is the first **real execution primitive** toward three-question accuracy.
It does not alter or weaken E1/E2's Host score authority: the App still shows
`NOT_RUN / NOT_SCORED` until a separately verified E2.5B integration exists.
The CLI performs a human-approved, single-fixture local SQL execution outside
of AppKit, without API key or network inference.

## Execution contract

1. Inspector loads a strict fixture JSON (`tia-postgres-fixture/v1`) and prints
   the **SHA-256 of the exact bytes**. No DB process is started.
2. Human checks table/column types, rows and expected outputs; a dummy fixture
   or one generated solely by AI is not sufficient accuracy evidence.
3. Operator runs with `--execute --approve-fixture-sha256 HASH --sql-file PATH`.
   Any change in bytes invalidates the approval.
4. Executor finds `initdb`, `pg_ctl`, `psql` from the **same** `pg_config --bindir`.
   It does not use `PGHOST`, `PGOPTIONS`, environment DSNs, default sockets,
   production schemas, or long-lived DBs.
5. In a private temporary directory it initializes a fresh cluster, sets
   `listen_addresses=''`, exposes only a 0700 local Unix socket, boots the
   human-reviewed fixture via the administrative bootstrap connection, creates
   `tia_candidate` with no superuser/DB-create/role-create permissions,
   grants SELECT over the fixture schema and enforces read-only transactions.
6. Executes one bounded SELECT/WITH as the restricted role with PostgreSQL's
   actual planner/executor; statement timeout and child process timeout apply.
7. Compares actual CSV rows deterministically against expected rows (including
   column aliases, NULL and duplicates; order only when explicitly required).
   Produces a typed verdict plus source question hash, fixture hash and SQL hash.
8. Stops the cluster in `finally` and deletes the private temp folder. A broken
   startup, missing server binary, failed approval or absent fixture fails closed.

## Limitations / important security qualifications

- This is **local practice isolation**, not VM/hypervisor containment for
  arbitrary adversarial code. If distributing to untrusted third parties,
  add OS-level sandbox permissions and independently review PostgreSQL role,
  extension and filesystem boundaries.
- The SQL guard is intentionally conservative, not a full SQL parser.
  A read-only, non-superuser database role inside a disposable cluster is the
  real authorization boundary.
- CSV display comparisons are not a complete SQL type semantics evaluator.
  One approved fixture yields only **0/1 or 1/1 local fixture pass**, never an
  official platform accuracy percent. More reviewed datasets are needed to
  test nulls, ties, duplicates, zero rows, and boundary cases.
- Candidate SQL is read from the local `--sql-file`, never inferred from the
  model's transcript. It is not automatically linked to a question until E2.5B.
- Automated Python tests mock the actual PostgreSQL subprocess. They **do not
  constitute live PostgreSQL integration evidence**. The real server gate must
  run on the user's Mac and record a separate approval and verdict.

## Server binaries check (no database operations)

```sh
BINDIR="$(pg_config --bindir)"
printf 'PostgreSQL binaries directory: %s\n' "$BINDIR"
for name in postgres initdb pg_ctl psql; do
  if test -x "$BINDIR/$name"; then echo "$name READY"; else echo "$name MISSING"; fi
done
```

## Demo fixture

`examples/bus_demo_fixture.json` is a *synthetic* Last Person to Fit in the Bus
problem with the correct demo result `Alex`. Its `question_sha256` is 64 `a`s:
**not** derived from an actual user question. This demo is never a real user's
rehearsal score.

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/run_sql_accuracy.py \
  --fixture integrations/virtual_technical_interviewer/engineering/s03e_postgres_accuracy/examples/bus_demo_fixture.json
```

Once the operator has reviewed the input and copied the exact SHA from the
preceding output, run the explicit test:

```sh
python3 -B integrations/virtual_technical_interviewer/scripts/run_sql_accuracy.py \
  --fixture integrations/virtual_technical_interviewer/engineering/s03e_postgres_accuracy/examples/bus_demo_fixture.json \
  --sql-file integrations/virtual_technical_interviewer/engineering/s03e_postgres_accuracy/examples/bus_demo_solution.sql \
  --execute --approve-fixture-sha256 "<REVIEWED_SHA256>"
```

Expected if all server binaries work: local PostgreSQL result `PASSED` with
`VERIFIED_LOCAL_FIXTURE`, exactly **one reviewed synthetic fixture**, no
other questions or official hidden tests. If server binaries are absent, expect
`NOT_VERIFIED / POSTGRES_SERVER_NOT_AVAILABLE` and do not pretend otherwise.

## Next required gates

- E2.5B: explicit native file selection and digest confirmation, binding to the
  *current* BYOQ question hash, controlled request/commit, typed SQL result
  surfaced on the question and frozen into evidence, preserving time limits.
- E3: Scorecard combines multiple independent reviewed fixtures, separately
  labels behavioral/communication rubric vs verified SQL pass ratio, Trainer
  receives only the frozen reviewed receipt. No model self-scoring.
- E4: three distinct confirmed questions → 45-minute real AI rehearsal →
  independent SQL tests → final receipt → review → Trainer → Human Gate.
