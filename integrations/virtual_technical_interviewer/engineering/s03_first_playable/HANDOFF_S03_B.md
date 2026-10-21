# S03-B local setup handoff — 21 October 2026

S03-A commit: `2f8d26226228218310379f8b39aed66515147f50`.
This increment extends that App; the final local commit SHA is reported in the
delivery response. Exact changed source paths are in `changed_sources.json`.

Build/open commands remain in `../../README_APP.md`. The actual bundle is
`integrations/virtual_technical_interviewer/dist/Technical Interview Lab.app`.
It is an unsigned local development build requiring system Python, not a released
standalone installer.

Implemented in the actual native/controller wizard:

- API Portal always precedes configuration. Native secure credential storage is
  session-only, consented, and explicitly **UNVERIFIED**. Empty/offline activation
  cannot enter setup. Credentials never cross into renderer/Python/save/export.
- Preparation of an unverified draft is allowed after local credential setup.
  This is an intentional visible preparation step, **not successful native
  authentication**; the directive's authenticated live-interview path remains gated.
- Exact 16 valid configurations, HARD only, 45→3 and 60→4, versioned draft digest.
- Editable bounded BYOQ import/review, exact slot count, missing/duplicate and
  dialect flags. Structural completeness never authorizes grading.
- Strict/supportive mechanism selection compiles source/role/policy digests;
  the host keeps full instructions, while the UI receives provenance metadata.
  Both evaluation profiles remain uncalibrated and numeric scoring disabled.
- Review/preflight blocks live launch on missing authentication and independent
  execution validation. Random generation's absent approved pool blocks launch.
  Disconnect clears native credential state and reblocks setup operations.

Final executable checks, all passed:

| Check | Result | Command / retained evidence |
|---|---:|---|
| TIA Python | 90 tests, including original 40 | `python3 -B integrations/virtual_technical_interviewer/run_tests.py` |
| TIA native | 67 checks | `bash integrations/virtual_technical_interviewer/scripts/build_app.sh` |
| Real WKWebView onboarding | 16 checks | bundled executable `--ui-self-test` |
| Full App reopen | 2 checks | bundled executable `--ui-recovery-test` |
| Real WKWebView setup | 10 checks | bundled executable `--ui-setup-test` |
| Shared HAL | 287 tests | S03-A `verification/S03-A/witness-hal.txt` |
| Witness native | 52 checks | same S03-A regression log |

Final reproducible command:
`python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --ui --increment S03-B`.
Exact command arguments, timings, zero exit codes and synthetic test receipts
are retained in `verification/S03-B/`. No tests failed or were skipped in these
executed suites. Witness/shared HAL source remains unchanged since the regression
run; those suites were not needlessly repeated for isolated TIA UI changes.

The setup journey entered a clearly named **synthetic, noncredential fixture**
through the actual AppKit secure field, reviewed three synthetic question records,
selected both mechanisms, and verified launch denial and disconnect. This is
not real provider authentication or Human UAT.

Remaining gates and scope:

- **Human App UAT: NOT_RUN.** Open the bundle, complete Guided Onboarding, test
  Back/Replay/Chinese/export, quit and reopen. Automation is not owner approval.
- **S04 dependency blocked:** no `psql`, `postgres`, `initdb`, `pg_ctl`,
  Docker/Podman on PATH or checked standard install paths; Postgres.app absent.
  No download or installation performed. Next smallest executable increment is
  one Hard PostgreSQL BYOQ fixture with real restricted execution and evidence,
  after an isolated PostgreSQL dependency is available.
- **S05 live AI: NOT_IMPLEMENTED / NOT_RUN.** There is no TIA network transport,
  live authentication, paid consent/request budget implementation, or adaptive
  provider conversation. Future live UAT requires explicit owner authorization.
- SQL/Pandas execution, randomized validated question generation, calibrated
  scorecard, complete Atlas policy, practice history and full shared HAL domain
  registration remain incomplete. This is not a claim of the whole v0.3 mission.
- Tutorial dialogue and Trainer preview are SIMULATED; SQL NOT_RUN; Technical and
  Communication independently NOT_SCORED. Real configuration questions are
  UNVERIFIED. No public push/release, paid request or real credential was used.
