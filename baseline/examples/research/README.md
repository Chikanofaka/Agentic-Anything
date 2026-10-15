# Research Diagnostics — Example Developer Harness

Purpose: take two nonnegative user-provided numeric inputs and compute gross proxy profit/margin. This is *not* a licensed investment tool or a valuation engine.

## Contents
- `harness.json`: declarative HAL demonstration manifest
- `main.py`: standard-library deterministic CLI
- `AGENTS.md`: domain role boundary
- `skills/research/SKILL.md`: calculation method

## Run in any Python 3.9+ terminal
```sh
python main.py --revenue 1500 --cost 900
```
Expected result: `profit: 600.00`, `margin: 40.00%`.

No HAL API key is needed for this deterministic example. If an IDE or Codex is used for further AI work, that host may require its own access/credentials. No real company or market data is bundled.
