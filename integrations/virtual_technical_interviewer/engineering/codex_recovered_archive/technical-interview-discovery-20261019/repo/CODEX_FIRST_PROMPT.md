# HAL-P2D-001 — Codex First Activation Prompt (Engineering DOING)

You are my implementing engineer for HAL (Harness Activation Layer), within the **already-approved, bounded DOING stage**. The current VS Code workspace contains a full product baseline under `baseline/` and a tested offline HAL Core under `runtime/`. **Do not create a brand new concept, PRD or dummy chatbot, and do not ignore the existing code.**

**Goal for this session:** start real local engineering using the existing artifacts: validate the baseline, perform a gap audit, then implement the smallest safe Sprint-1 HAL core improvement that preserves Type A / Type B domain-package interoperability. We should be able to hand a domain-specific package to HAL, inspect its manifest, reject unsafe/incompatible packages, execute only pre-registered offline tools, and receive truthful receipts. The HTML Ready MVM is a reference for eventual UI integration, not proof of live AI.

**Read all of these before coding, in this order:**
1. `AGENTS.md`, `README_START_HERE.md`, `status/HUMAN_GATE.md`.
2. `baseline/prd/NEED_NORMALIZED.md`, `baseline/prd/HAL_PRD_v2_0.md`, `baseline/prd/TRACEABILITY.csv`, `baseline/prd/UAT_MATRIX.md`, `baseline/prd/ASSUMPTIONS_AND_OPEN_QUESTIONS.md`, and `baseline/prd/ARCHITECTURE_OPTIONS.md`.
3. `baseline/CODEX_HANDOFF.md`, `baseline/skill-feedback/PILOT_RECURSION.md`; inspect the `baseline/ready-mvm/index.html` UX and two `baseline/examples/` packages.
4. `runtime/README.md`, `runtime/docs/CODEX_NEXT_ENGINEERING.md`, `runtime/docs/SECURITY_AND_LIMITATIONS.md`, then review the actual code and tests inside `runtime/hal_core/`, `runtime/trusted_adapters/`, and `runtime/tests/`.

**Now execute:**
A. In terminal, first run `python3 --version`, then `bash scripts/verify_local.sh`. Record the test count, success/failure, generated sample output, and any environmental blocker. The Manus preflight is intentionally blocked and not a failed feature.
B. Create `engineering/BASELINE_AUDIT.md` mapping PRD FR requirements → current implemented module → missing capability → negative tests → Sprint-1 plan. Identify the minimal enhancement that can be completed locally without additional permission.
C. Then **implement** the first safe vertical slice, ideally normalizing a single-top-folder GitHub ZIP and strengthening package manifest/port/security validation. Update tests and documentation. Do not stop after only planning unless a blocker makes safe implementation impossible.
D. Run the full regression and negative tests. Save an inspectable `engineering/SPRINT1_RECEIPT.md` with exact commands, before/after results, changed files, failures and debt. Avoid claiming real provider compatibility based on simulated preflight.
E. Finish with a concise handoff and what I should click/enter next as Human.

**Absolute limits (not negotiable):** no public GitHub, `git push`, remote repository creation, live API keys, paid model inference, cloud deployment, external writes, arbitrary downloaded code execution, unapproved network access, or silently installing dependencies. For model connectivity, write only mocks/contracts and clearly label simulated behavior. The PRD Compiler v2.1 is a candidate, not an automatically installed or promoted skill.

Human Gate = DOING, **not** publication approval. We will decide the first real third-party repository and provider separately after local proof. Please start by reading the files and running the smoke tests now; then continue to bounded implementation.
