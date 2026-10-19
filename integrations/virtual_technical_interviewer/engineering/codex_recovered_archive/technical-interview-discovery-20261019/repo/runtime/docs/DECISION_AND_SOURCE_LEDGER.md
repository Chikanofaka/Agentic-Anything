# Engineering Architecture & Lineage Decisions

Sources: current user DOING approval (2026-10-14); prior `HAL_Pilot_v2_0/prd/HAL_PRD_v2_0.md`, `TRACEABILITY.csv`, `UAT_MATRIX.md`, `ARCHITECTURE_OPTIONS.md`, `CODEX_HANDOFF.md`, `skill-feedback/PILOT_RECURSION.md`, and two `examples/{research,returns}` fixtures. Previous Trello PRD and Ready records are preserved.

| Decision | Rationale | Truth status |
|---|---|---|
| Local Python stdlib for Sprint 0 | reproducible runtime contract without installs, service provisioning or secrets | RESEARCH/RETURNS DETERMINISTIC PROOF ONLY |
| Curated tool registry separated from HAL Core | proving reusable dispatch and fail closed behavior without executing imported code | IMPLEMENTED |
| Import package ZIP/dir as inspected data | validates schema and content digest; guards traversal before anyone handles raw repo ZIP | IMPLEMENTED (not malware scan) |
| Split `LLM_DIRECT` from managed-agent ports | prevents Manus/WorkBuddy-style task endpoints being interpreted as bare model completion | IMPLEMENTED OFFLINE CONTRACT; NO REAL API CALLS |
| No native keys or browser-runtime bridge yet | user explicitly prohibits real secret usage; OS/distribution platform unresolved | UNIMPLEMENTED |
| Preserve Skill v2.1 as candidate | recursive change requires human review, does not automatically overwrite current Skill | PROPOSAL ONLY |
| No external repo access / publish | external repo, license, and authorization not selected; user denies public publication | NO PUBLICATION |

**Decision provenance:** User authorized **DOING** for engineering on this task, not secret usage or external release. Original PRD stage was **Idea**; original Ready state was `READY_FOR_HUMAN_UAT_WITH_DEBT`. Trello moved the v2 Ready card into **Doing** and retained descriptive evidence/comments. No historical source rewritten.
