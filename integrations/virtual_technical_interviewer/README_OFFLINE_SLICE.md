# TIA offline executable slice

Run from the repository root (Python standard library only; observed Python version is recorded in the receipt):

```sh
python3 -B integrations/virtual_technical_interviewer/offline_demo.py
python3 -B integrations/virtual_technical_interviewer/offline_demo.py --json
python3 -B integrations/virtual_technical_interviewer/run_tests.py
```

The CLI runs one deterministic synthetic interview, closes and freezes its event receipt, records an explicit scripted handoff review, assigns a separate Trainer drill, then completes the demonstration. Repeat runs produce the same JSON. Normal controller use defaults to a host monotonic clock; the demo explicitly injects a fixture clock.

Implemented source:

- `agents/interviewer/` and `agents/trainer/`: separate identity, soul and role instructions, validated by `tia_runtime/contracts.py` and `agents/roles.json`.
- `tia_runtime/provider.py`: provider-neutral request/response interface, default offline mock, cancellable timeout, validated output and sanitized errors. `FutureOpenAIAdapter` is disabled and has no credentials, SDK or transport. `--provider openai` returns a blocked error with exit 2.
- `tia_runtime/controller.py`: `NEW → INTERVIEWING → CLOSED → REVIEWED → TRAINING → COMPLETE`, host-owned event sequence/time, bounded candidate input, closed receipt digest and separate reviewer/Trainer handoff. Failed model replies preserve already committed candidate actions. Returned snapshots are copies.
- `offline_demo.py` and `tests/`: executable demonstration and regression/negative tests.

Technical and Communication have separate evidence references and remain `NOT_SCORED`. Proposed code and test descriptions are `NOT_EXECUTED`; there is no SQL evaluator, grading formula, live model, autonomous capability judgment or claim of training effectiveness. The scripted review only checks handoff eligibility; it is not human rubric calibration.

This is a TIA specialist controller following HAL's trusted-host pattern, contained in this integration. It does not alter the shared HAL registry, claim generic package activation, or reuse Witness's full-state export as a confidentiality boundary. Role documents are data; they do not grant runtime permissions. In-memory state has no restart persistence, remote authentication or protection against the local process owner. A SHA-256 digest is not a signature.

Source authority: the current bounded implementation request and `TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md` (FR-03/04/05/08/12/27, COM-FR-001/007/009/010/012). This slice provides selected mechanisms, not full acceptance of those requirements or completion of M0. Existing S02/rebase artifacts and their `NOT_RUN` statuses are preserved. See `engineering/offline_slice/HANDOFF_RECEIPT.md` for actual commands/results.
