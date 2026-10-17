# Witness Loop domain package

Path A: open the HAL workspace in an IDE and read `trusted_adapters/witness.py`,
`tests/test_witness_v2.py`, `tests/test_character_context.py` and this manifest. The reviewed host adapter owns
the rules. This package is declarative input; importing it never runs `main.py`.

Path B: the local HAL Witness app uses the same reviewed transitions, scene and
evidence rules, with optional provider narration. Without a provider, narration
is explicitly deterministic. Free conversation does not consume six case turns.

New sessions use `witness-state/v2`: case brief, narrator, empty platform,
deliberate inspection, witness entrance, then alternating NPC/player turns.
Visible objects are not collected evidence. The physical clock reading is
authenticated as an observation; it is not an authenticated departure log.
The clock/call link is a working investigative hypothesis, not proof of an
exact departure time. Three bounded game outcomes remain available.

The canonical editable story sources are `integrations/witness_loop/source/`.
Run `python3 scripts/compile_witness_character.py`, then rebuild the Mac app.
Only explicitly selected reviewed sections enter the versioned runtime artifact;
the complete director story is never a model prompt or player briefing.
The runtime reports effective context and source digests. The duplicate
`WTL-029_Witness_Loop_v0.1/` authoring copy is checked for drift, not loaded.

The host preserves player statements, observations, commitments and admissions
as separate provenance. A v1 save is migrated to a separate v2 save while its
original file is retained. Previously acquired clock/ticket clues are labeled
`LEGACY_V1_ACQUIRED`, never represented as fresh inspections. Historical v1
rules and regression tests are preserved in `witness_v1.py`.

The LLM proposes intent and language. The reviewed host requires explicit case
action confirmation and validates testable identity/disclosure violations
before storing a reply. Pattern checks are bounded safeguards, not complete
semantic proof. No external files, network, accounts or arbitrary source
execution are granted by this package. Provider credentials stay in the native
host and never enter this domain's context, state or exported memory.
