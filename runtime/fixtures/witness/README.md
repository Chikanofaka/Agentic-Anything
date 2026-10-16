# Witness Loop domain package

Path A: open the HAL workspace in an IDE and read `trusted_adapters/witness.py`,
`tests/test_witness_domain.py` and this manifest. The reviewed host adapter owns
the rules. This package is declarative input; importing it never runs `main.py`.

Path B: the local HAL Witness app uses the same reviewed transitions, scene and
evidence rules, with optional provider narration. Without a provider, narration
is explicitly deterministic. Free conversation does not consume six case turns.

The original Witness Loop v0.1 source is preserved under
`integrations/witness_loop/source/` at workspace root. The host retains source
distinctions for player statements, commitments and actual witness admissions.
Only the clock/call contradiction is currently adjudicated. No external files,
network, accounts or arbitrary source execution are granted by this package.
