# Trainer contract

- Preconditions: the host has closed the interview, explicitly reviewed the immutable receipt and initiated the Trainer handoff. A candidate message or provider response cannot authorize this transition.
- Input: only the reviewed receipt supplied by the host, containing permitted evidence and its digest. No active interview state, answer bank, credentials or raw provider internals.
- Output: a bounded coaching reply with one proposed drill. It is not a score update or permission to change the next session.
- Authority: no state mutation, scoring, test execution, answer-vault access, interview activation, provider selection or credential access.
- Runtime: the bundled deterministic mock is offline and has no external tools.
- Retention: this slice does not create a longitudinal personal profile or send reminders.

Enforced contract: `agents/roles.json` and `tia_runtime/contracts.py`; session authorization belongs to the controller. Source: v3 §§15, 18(W09), 19 and 28.
