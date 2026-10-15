# HAL v2 · Minimum Viable Ideation — Diverge → Evaluate → Converge

**Need winner (user-stated, not market validated):** make developer-native expertise usable across developer and consumer contexts without repeatedly building onboarding and credential/runtime infrastructure.

| Candidate | Product mechanism | Outcome fidelity | Integration burden | Security complexity | Selected? |
|---|---|---|---|---|---|
| I0 GitHub README generator | summarize code and provide ZIP links | Helps Path A only | Low | Low | No — no B activation |
| I1 BYOK chat overlay | universal chat box layered on any site | Poor: domain actions not bound | Low–med | High | No — decorative AI |
| I2 Website-only proxy | hosted agent runner + store | Real B but deviates local-first/ownership goal | High | High | No |
| I3 **HAL Domain-Swap Studio** | same shell reads package contract; Path A developer export; Path B capability-aware domain tools | **Directly proves A/B and reuse hypothesis** | Medium (curated packages only) | Bounded in simulated MVM | **YES (relative candidate)** |
| I4 Auto-convert any GitHub ZIP | inspect and execute arbitrary scripts | Attractive promise, unsafe/unreliable v0 | Very high | Very high | No |

**Reason I3 wins:** smallest faithful slice that demonstrates shared-shell integration of two distinct domains, with safe no-key education, real local domain calculations and transparent simulated AI preflight.
**Killer assumption:** maintainers can adapt a second unrelated domain using manifest + bindings faster than authoring a bespoke consumer app, without distorting domain workflow.
**Cheapest falsifier:** give Codex two audited source harnesses; compare integration person-hours versus bespoke and independently evaluate quality. The two demo fixtures are not substitutes for this future engineering evidence.
**Decision status:** PROPOSED, HUMAN_GATE=PENDING; this is NOT a market-supported winner.
