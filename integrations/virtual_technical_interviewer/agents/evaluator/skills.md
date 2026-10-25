# Evidence-linked evaluation skills — v1

Canonical rubric: TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md §14A; numerical source RUBRIC_60_40_PROPOSAL.json, bundled byte-for-byte as policy/evaluator_rubric_v1.json.

Technical:
- T01 Solution correctness and output integrity: deterministic tests, state invariants, actual outputs. Host permits a proposal only for the latest verified PASSED or FAILED SQL submission. FAILED is observed counterexample (anchor 0), not successful correctness. PASSED covers one local fixture only.
- T02 Technical model and algorithmic understanding: correct SQL/function semantics, causal explanation, alternatives.
- T03 Planning/decomposition and requirement coverage: task breakdown, edge-case planning, complexity tradeoffs.
- T04 Testing/debugging/repair: reproducible diagnosis, before/after attempts, root-cause isolation.
- T05 Resource efficiency and maintainability: time/space tradeoffs, data cost, explainable design.

Communication:
- C01 Clarification and expectation alignment: restatement, relevant question, acknowledged answer, correct action.
- C02 Explainable plan and in-flight narration: coherent why/how, useful progress updates.
- C03 Progress/evidence narrative: faithfully distinguishes completed, unverified and unfinished work.
- C04 Gap-to-action translation and bounded assistance request: exact unknown, independent attempt, policy-aware request.
- C05 Feedback integration and collaboration-to-execution: cue followed by verifiable code/test/plan revision. Only cited post-reply candidate actions are eligible; chronology alone does not prove integration.
- C06 Professional closure/synthesis: limitations, solution and next step. No explicit closing-speech event exists in this slice: MUST abstain. A submit button is not closing speech.

Use the canonical proposed anchors. Anchor 4 requires unfamiliar-case evidence unavailable in this slice, so use null or 0–3 only. Observed anchor 0 requires an actual cited counterexample. No citation means null, not zero. Be conservative with truncated context; abstain where evidence is inadequate. Assistance status is NOT_ESTABLISHED unless the host has verified it, and no before/after improvement claim follows from a mere sequence.

For each criterion return [dimension_id, anchor_or_null, [candidate_aliases], brief_reason]. Exactly 11 ordered rows T01,T02,T03,T04,T05,C01,C02,C03,C04,C05,C06. Use only the supplied allowed_aliases for that dimension, never invented IDs or interviewer text as candidate evidence. Null anchors require empty citations. Reasons should be 8–60 characters. Return EXACTLY {"assessments":[...]} with no Markdown or extra keys. Keep the full reply under 2000 characters.

The host computes proposed_points=max_points*anchor/4 for observed dimensions only. No renormalization, no aggregate across axes, no final score. These are provisional arithmetic proposals, not calibrated assessments. Return uncertainty in the brief reason when declining to assess.
