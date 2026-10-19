# Proposed Skill v2.1 rule extension — derived from HAL v2 Pilot

This is a **candidate patch** requiring human review, not an installed/automatically learned rule set.

## Seven new invariant compiler checks
1. **Section specificity:** After generating every master-template chapter, identify one unique decision served, exact evidence inputs, concrete artifact, and falsifier. Flag if prose is interchangeable with another chapter.
2. **Dual states:** Keep `user onboarding task completed` separately from `provider/agent currently connected`; progress metrics and operational readiness may diverge.
3. **Stale result prevention:** Every stateful input/output system requires a rule for invalidating, versioning or explicitly labeling outputs after relevant inputs change or become invalid.
4. **Port capability verification:** Every claimed 'intelligent' feature maps to a typed model/managed-agent/tool/data contract. Semantic/credential compatibility is assumed false until tested.
5. **Direct-fidelity escalation:** A consumer MVM must make the reusable value mechanism inspectable, not only show a static workspace or generic chat panel. For a platform/harness product, include **two deliberately different domain integration examples**, or document why one is sufficient.
6. **Evidence tier separation:** Track Documentation Completeness, MVM Functionality, Security/Engineering Validation, Real Customer Validation separately; none substitutes for another.
7. **Skill proposal cannot self-promote:** Automated evaluation may propose a patch and regression suite, but changes to the authoritative Skill and project Done/publishing stages require explicit human signoff.

## Before marking PRD complete
- Inspect all 32 sections: if the required artifact is absent, mark OPEN/N/A with explanation rather than inserting generic boilerplate.
- For every FR: `Need → JTBD → Workflow → Input → Tool/Permission → Output → Negative Test → Evidence → Owner` must exist in trace matrix.
- For each new mockup: run success, bad input, denial, disconnect, changed-input/stale-output and source ZIP validation.
- Compare changed thesis to v1 baseline and record why the new design is worth the additional complexity.
- Enumerate what is built, simulated, hypothesized, out of scope, and blocked; keep the labels on page and receipt.
