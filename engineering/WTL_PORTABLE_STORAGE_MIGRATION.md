# WTL-029 Portable Beta — Storage Migration (development branch)

This phase relocates **new app player saves** to `~/Library/Application Support/Witness Loop/`, and removes the local repository absolute path from the bundled `config.json`.

**Not a portable release yet.** The native worker still starts `/usr/bin/python3`, and signing/notarization/sandbox verification are pending. Do not distribute the generated unsigned .app.

## Safe migration sequence (Mac)

1. **Quit Witness Loop completely.** Keep your independent Desktop backup.
2. Pull this feature branch, verify working tree clean, and inspect the migration preview:

```bash
git fetch origin
git switch feat/wtl029-portable-beta
git pull --ff-only origin feat/wtl029-portable-beta
/usr/bin/python3 scripts/migrate_witness_saves.py
```

3. Only when the preview lists expected save names/hashes, and the game is closed, explicitly copy:

```bash
/usr/bin/python3 scripts/migrate_witness_saves.py --apply
```

**The script never overwrites a destination save.** If the target already holds `session-v2.json` or `session.json`, it stops; do not remove or overwrite that file. It copies only those two allowlisted filenames, validates JSON envelope schema and duplicates, refuses symlink save files, and leaves the originals untouched. The HAL Core checks the full state/receipt contract when the rebuilt app starts. A dry run does not create a target directory.

4. Rebuild and run local regressions, without entering credentials:

```bash
bash scripts/verify_witness_local.sh
"integrations/witness_loop/dist/Witness Loop.app/Contents/MacOS/WitnessLoop" --ui-self-test
open "integrations/witness_loop/dist/Witness Loop.app"
```

5. Verify your case progress, Lin Wu's conversation history, acquired evidence and verdict state. Check the new save under `~/Library/Application Support/Witness Loop/`. Do not post save contents or API secrets publicly.

## Boundaries

- The migrated original remains in `integrations/witness_loop/data/` as a backup. No automatic import happens on launch.
- GUI smoke saves and screenshots use a unique temporary directory and never load player saves.
- If migration or launch fails: quit, preserve both directories unchanged, and share only error messages (not private saves) for diagnosis.
- No Mac-native compilation or actual-player UAT has been executed by the remote source edits; both are local acceptance gates.
