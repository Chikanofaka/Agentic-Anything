
# Retrospective local SQL verification

The final report now offers three reviewed synthetic PostgreSQL case suites for the imported delivery, monthly transaction and bus questions. This is a separate post-interview observation. Original sessions, submissions, timing and model assessments are preserved.

## Human UAT

1. Finish a three-question PostgreSQL rehearsal with a submitted SQL answer. Reopen an archived completed rehearsal if desired.
2. Select the completed question and the appropriate synthetic suite. Review its assumptions, input tables and expected rows. Source matching is an explicit human decision: title similarity is never treated as proof that a suite applies.
3. Choose the local test action and confirm the native sheet. It binds the question, frozen record, latest SQL and exact suite hashes. No OpenAI call occurs.
4. Inspect each case and the aggregate. PASSED/FAILED are actual PostgreSQL output comparisons. EXECUTION_ERROR is a query error. NOT_VERIFIED means the local runner or supported execution was unavailable. These finite cases are not official hidden tests or exhaustive correctness proofs.
5. A previously committed AI assessment is preserved in the assessment archive; the new execution evidence requires a new explicit evaluation. Model evaluation still needs separate native paid-request consent. Opening the report or replaying history performs no SQL or API work.
6. Cancel an in-flight local test. A late result must not commit. Restart during a pending test; recovery cancels instead of executing again. Old journal records remain readable.

## Boundaries

The renderer can request review, execution and cancellation but cannot call private prepare/commit/reject commands. Native owns process cancellation. The worker starts a private process group, unwinds temporary PostgreSQL cleanup on SIGTERM and has a bounded native hard-stop fallback for the worker and child commands still in its process group. PostgreSQL may daemonize outside that group; normal shutdown uses the runner’s finally cleanup. If cleanup itself wedges, the hard-stop bounds the worker but cannot guarantee daemon cleanup. Cancellation UAT must also inspect for leftover temporary PostgreSQL processes. Each ephemeral database uses the existing single-statement read-only runner and fixed approved PostgreSQL paths; no remote database is accepted. Candidate SQL travels on stdin, never process arguments. Expected rows are authored deterministic fixtures, not model-generated answer judgements. Submitted code and suite observations are kept separately from private reference answers.

Every completed attempt is retained in post_interview_sql.observations. results contains the latest attempt for each question; assessment_archive retains superseded AI proposals verbatim. A new unavailable attempt is reported as NOT_VERIFIED, with earlier observed results still in the retained attempt history. Formal grades remain separate authorization.

## Automated checks

Run the ordinary host tests with tests/test_post_interview_sql.py. It covers source/code/suite mutation, real-execution metadata projection, wrong answers versus missing runner, duplicate/late generation rejection, history preservation, evaluator invalidation, rejection diagnosis, replay and restart cancellation. Synthetic runner tests never claim actual database correctness.

An additional opt-in test file tests/test_post_interview_sql_local.py runs fixed positive and negative SQL examples against these authored suites using the installed ephemeral PostgreSQL runner. Enable only with TIA_RUN_LOCAL_POSTGRES_TESTS=1; it makes no provider requests and uses no user database.
