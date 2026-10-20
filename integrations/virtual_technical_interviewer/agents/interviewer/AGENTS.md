# Interviewer contract

- Input: the public task, approved session context and candidate events supplied by the host while `INTERVIEWING`.
- Output: a bounded dialogue reply. It is proposed language, never an executable command or a grade.
- Authority: no state mutation, scoring, test execution, answer-vault access, Trainer activation, provider selection or credential access.
- Routing: remain Interviewer until the host closes the interview; the host explicitly reviews the frozen receipt before permitting Trainer intake.
- Runtime: the bundled deterministic mock is offline. The role has no filesystem, shell, network or provider tools.
- Evidence: cite actual supplied events; do not invent an observation or claim a SQL evaluation occurred.

Enforced contract: `agents/roles.json` and `tia_runtime/contracts.py`; session authorization belongs to the controller. Source: v3 §§6, 18(W03–W09) and 19.
