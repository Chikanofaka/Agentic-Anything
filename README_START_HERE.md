# HAL-P2D-001 — VS Code + Codex First-Run Workspace

**Status:** Human Gate = DOING (authorized 2026-10-14), not a public release.
**Scope:** Real local offline HAL Core; no real AI inference or credential storage exists yet.

## 1. Open the folder
In VS Code choose **File → Open Folder…** and select this entire `HAL-P2D-001` directory (the folder containing this file, `AGENTS.md`, `baseline/`, and `runtime/`). You do **not** need to upload images, paste the PRD, or import separate ZIPs into Codex.

## 2. Verify the existing engineering baseline
Open VS Code Terminal → New Terminal, check:

```bash
python3 --version
bash scripts/verify_local.sh
```

Python **3.10+** is the recommended baseline. The verifier reports the actual interpreter and can record observed compatibility on 3.9. If Python is unavailable, diagnose locally; never install dependencies silently. The script performs zero network/model calls.

The preserved Sprint 0 baseline had 31 passing tests. Sprint 1 adds schema, archive, typed capability and CLI regression/security tests; see `engineering/SPRINT1_RECEIPT.md` for the current count. The verifier asserts Research revenue 1500/cost 900 -> profit 600/margin 40.0%, Returns sealed/proof yes/5days -> STANDARD_RETURN, and the actual Manus CLI denial with exit code 2.

Environment evidence: this workspace currently provides Python 3.9.6, which passes the recorded checks. Python 3.10+ remains recommended; the broader version/OS support matrix is unverified. No dependency installation is needed or attempted.

## 3. Start Codex
Open the **Codex** chat pane in VS Code. Paste the full content of `CODEX_FIRST_PROMPT.md`. It gives the agent an ordered reading plan, execution mandate, explicit prohibitions, and evidence/acceptance rules.

Use **the current local workspace** rather than starting a cloud task or opening an empty unrelated repo. If asked to authorize shell operations, review that they are inside this folder and do not involve credentials, paid APIs, external writes or publication.

## 4. Preview the original consumer MVM
Open `baseline/ready-mvm/index.html` in a browser. It is an offline simulation; **never paste a real API key** into it.

## 5. Git — optional local only
If you need version history, let Codex initialize a **local** Git repository in this folder (`git init`) after reviewing `.gitignore`. DO NOT create a remote or run `git push` without separate Human approval.

## Where everything is
- `baseline/prd/HAL_PRD_v2_0.md` — approved product requirements, 32 chapters
- `baseline/prd/TRACEABILITY.csv` & `baseline/prd/UAT_MATRIX.md` — requirement/test contracts
- `baseline/ready-mvm/index.html` — simulated consumer UX reference
- `baseline/skill-feedback/PRD_Compiler_v2_1_CANDIDATE/` — **candidate**, not promoted skill
- `runtime/README.md` — offline Core startup instructions
- `runtime/hal_core/`, `runtime/trusted_adapters/`, `runtime/tests/` — actual code and tests
- `runtime/docs/CODEX_NEXT_ENGINEERING.md` — next implementation priorities
- `AGENTS.md` — local Codex operating constraints
- `status/HUMAN_GATE.md` — authorization and stage reality

## Do not confuse these three phases
Ready MVM = credible consumer simulation; Sprint 0 = **real deterministic** offline runtime with curated local adapters; next Sprint = continued engineering, not authorized production inference.
