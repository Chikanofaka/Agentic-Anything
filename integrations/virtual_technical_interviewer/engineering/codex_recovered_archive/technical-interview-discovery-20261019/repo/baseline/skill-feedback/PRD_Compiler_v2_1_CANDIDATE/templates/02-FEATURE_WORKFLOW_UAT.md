# Feature → Workflow → Test contract

## Feature FR-{ID}
- Need link: NEED-{ID}, evidence [reference], user [persona].
- JTBD and trigger: [when / goal / current substitute].
- Priority: Must/Should/Could with critical-path rationale, not just urgency label.
- Preconditions and authorizations: [identity, data grants, approved external writes].
- Input contract: [schema, required fields, provenance, freshness, validation, empty case].
- Deterministic rules: [fixed business logic, thresholds and edge cases].
- Adaptive rules (optional): [model capability, prompt/domain policy, tools and grounding].
- State graph: Not configured → Ready → Running → Needs review → Completed / Failed / Cancelled.
- Output contract: [format, destination, acceptance, source links, revision].
- Error and recovery: [timeout, invalid input, unavailable provider, revoked grants, partial result].
- Telemetry: [status, latency, trace, cost, quality], no secrets in logs.
- Verification: Given [fixture], When [action], Then [observable output]. Negative: Given [forbidden/invalid case], Then [denial/no side effect].

## Workflow node
`NODE_ID | actor | trigger | inputs | processing/skills | output artifact | precondition | timeout/retry | evidence | human gate | next state`.

## UI screen
`SCREEN_ID | entry route | primary goal | controls | context | business computation | success | empty | error | recover | accessibility | REAL/SIMULATED/ASSUMED`.
