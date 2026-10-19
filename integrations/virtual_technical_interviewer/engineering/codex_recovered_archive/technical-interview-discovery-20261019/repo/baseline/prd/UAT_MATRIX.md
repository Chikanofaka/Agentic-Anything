# HAL v2 — Feature → Workflow → Real/Negative UAT Contract

**Test levels:** R=real deterministic Ready/browser, S=simulated Ready, D=Doing only. Every feature has *at least one adverse test*. Completion must produce observable evidence, not screenshots alone.

| UAT | FR | Given → When → Then (positive) | Adverse / denial | Mode | Evidence |
|---|---|---|---|---|---|
| T01 | F01 | new user chooses A/B → correct page opens and returns | reset from any page does not leak mode | R | browser check + screenshot |
| T02 | F02 | select Returns → shell displays Returns UI, README, bindings | unknown manifest may be inspected but NOT executed | R | DOM + JSON fixture |
| T03 | F03 | developer chooses Research → rendered documented prerequisites | absent README should produce invalid-package error in Doing | R/D | README + export, contract audit |
| T04 | F04 | download ZIP → contents include manifest, agent, skill and CLI | secret scan/path traversal must block publish | R/D | zipfile.testzip() + source audit |
| T05 | F05 | 4 correct lessons → four completion flags | wrong answer prevents Next | R | Chromium interaction |
| T06 | F06 | OpenAI demo preflight → **SIMULATED PASS** | Manus direct slot → `MANAGED_AGENT_PORT_MISMATCH` / no activation | S | DOM status |
| T07 | F07 | switch Research→Returns without shell reload → domain native controls change | unknown domain cannot receive tool execution | R | DOM controls / manifest fixture |
| T08 | F08 | research 1500/900→600/40%; returns sealed yes 5→STANDARD_RETURN | revenue=0, days<0→reject and invalidate old output | R | CLI + browser assertions |
| T09 | F09 | demo enabled + real specialty outcome → scripted insight labeled SIMULATED | no active demo or missing domain run → no insight | S | DOM tag; no fetch |
| T10 | F10 | selected domain shows binding/port/readiness matrix | lacking tool/provider must not appear READY | R/D | JSON diagnostics; integration tests pending |
| T11 | F11 | export report, manifest, diagnostics, source ZIP, UAT JSON | export without successful domain run blocked | R | downloaded artifact names/bytes |
| T12 | F12 | Human gate feedback → local JSON includes decision and scores | unset decision remains PENDING; never auto-publishes | R | browser UAT |
| T13 | F13 | invalid input corrected → successful retry; disconnect → deterministic retained | repeated invalid must not create stale/current report | R | browser checks + no side effects |
| T14 | F14 | native key vaulted, model authenticated | renderer/log/ZIP/raw key exposure prevented | D | native negative security tests pending |
| T15 | F15 | allowed real model uses typed specialist tool & produces receipt | external write without consent blocked, task budget cap enforced | D | trace/denial receipts pending |
| T16 | F16 | two distinct genuine repos integrated without HAL core changes | if rewriting HAL core needed, generality criterion FAIL | D | measured source diffs/engineer-hours pending |

## Acceptance boundary
T01–T13 are Ready-level or explicitly simulated; T14–T16 are engineering validation commitments, not completed tests. Passing all demo tests is NOT evidence of model integration, enterprise security or market acceptance.
