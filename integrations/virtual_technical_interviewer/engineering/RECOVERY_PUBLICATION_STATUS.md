# TIA Codex recovery publication status

- Original source files/symlinks verified into private local backup: **1006**.
- Archive records: **1014**.
- Sanitized files copied to the recovery archive: **196**.
- Deduplicated against existing repository content: **68**.
- Binary/unreviewed type excluded from public mirror: **700**.
- Build/VCS metadata excluded from public mirror: **46**.
- Large compiler cache files excluded: **4**.
- Existing staged whitespace warnings: **538** (preserved, not automatically rewritten).
- Earlier missing Markdown references in the v3 review package: **0**.

This public branch is a **sanitized, selective mirror**, not a byte-identical archival upload.
The complete byte-identical snapshot is retained only in a private local backup.
No recovered historical test result is treated as a current TIA UAT pass.
See `codex_recovered_archive/MIGRATION_MANIFEST.json` for individual file decisions.
