# TIA Codex repository-first policy

- Always start work at `~/Developer/Agentic-Anything`, on a named feature branch; treat this Git repository as the source of truth.
- All final design documents, code, plans, tests, receipts, provenance, and handoff notes belong inside the appropriate repository directories.
- `/private/tmp/` may be used for disposable execution scratch only; copy every durable result back into the repository before declaring completion.
- Keep credentials, personal data, real user logs, and raw local paths out of the public Git history. Archive raw originals privately and publish sanitized evidence.
- Never silently fabricate test results or upgrade TIA scenarios marked `NOT_RUN` to passed. Preserve original version provenance.
- Before push, run relevant tests, link/integrity checks and review `git diff --cached`; request human approval for live network/API calls or irreversible actions.
