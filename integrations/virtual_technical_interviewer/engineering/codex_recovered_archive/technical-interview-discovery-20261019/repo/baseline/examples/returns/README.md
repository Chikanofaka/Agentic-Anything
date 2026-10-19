# Returns Operations — Example Developer Harness

Purpose: show that one HAL Shell can swap to a distinct specialty workflow. No personal data, warehouses, real order records or external integrations.

## Deterministic triage policy
- Missing purchase proof → `MANUAL_REVIEW`.
- Damaged or opened parcel → `INSPECT`.
- Sealed parcel with proof and age <= 30 days → `STANDARD_RETURN`.
- Otherwise → `OUT_OF_WINDOW`.
This is a fictional demo rulebook, not an actual retailer's policy.

## Run in any Python 3.9+ terminal
```sh
python main.py --condition sealed --proof yes --days 5
```
Expected `STANDARD_RETURN`. No LLM API key or external service is needed for this demo.
