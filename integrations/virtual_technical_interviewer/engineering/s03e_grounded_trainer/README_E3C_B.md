# S03-E3C-B — Native BYOK AI Trainer / Model proposal

**Parent (GitHub)**: `849a917af9de4fcd8d36a562b997c6104d309b0f` (E3-C-A).
**Target**: `feat/tia-s03e-e3cb-native-ai-trainer`.
**Stage**: source-integrated candidate, human Mac verification required; not an authorized merge or release.

## Trust boundaries

1. The renderer can only request `trainer_request` with `{}`. It cannot send an API key, role, source hash, model output, grade, consent or native worker commit. `BridgePolicy` rejects `native_{prepare,commit,cancel}_trainer` actions.
2. The native `NSAlert` requires **per-request human confirmation**, even when API Portal has previously obtained paid consent. It shows the frozen selected drill ID/digest and the exact sharing limits. Cancelling returns without initiating any paid model call.
3. A validated completed three-question rehearsal and nonempty E3-C-A drill list are required. Host snapshots/export never call the model or database.
4. The native Python Host prepares the exact evidence subset: one drill plus cited candidate event excerpts (max 280 characters each; this **can include a short SQL query in full**), no full fixtures, no credential, no unrelated task. The model's untrusted input is bounded to 16KB and receives *no system authority*.
5. The native-only `TIAModelRequest` uses role `trainer`, `tia_trainer_reply`, fixed HTTPS endpoint and 600 output tokens. Its JSON `reply` string carries a strictly parsed, schema-constrained **proposal** with selected drill ID, exact refs and hashes, text for hypothesis/action/acceptance/uncertainty.
6. Host commit re-checks transaction ID, generation, source digest, **exact source packet digest**, candidate event IDs, fixture binding, single-source drill, text constraints, selected model and usage shape. Unauthorized `authoritative_score`, fabricated refs, duplicate JSON fields or changed source are refused. Source-bound local receipt is `PENDING_HUMAN_REVIEW`, `authority=NONE`, `semantic_truth=HUMAN_REVIEW_REQUIRED`.
7. A native model request may have been billed even on timeout/cancellation. If the App crashes after prepare, startup writes `native_cancel_trainer` and shows interruption. There is no background retry or generation on reopen; a new user action and fresh consent is mandatory. A successfully committed proposal is loaded locally and never automatically regenerated.
8. E3-A technical scorecard, E3-B C01–C06 observation, original SQL PostgreSQL receipt, S03-E2 time ledger, and existing persisted digest authority are unmodified.

## Automated gates

```bash
python3 -B integrations/virtual_technical_interviewer/run_tests.py
python3 -B integrations/virtual_technical_interviewer/scripts/verify_app.py --increment S03-E3CB --ui --regressions
echo "E3CB_MAC_GATE_EXIT_CODE=$?"
```

Native WebKit step: `native-byok-trainer-webkit` builds the actual macOS App, presents a synthetic native consent dialog, follows 3-question BYOQ and real local PostgreSQL verification, then routes a single role-separated *mock HTTP* Trainer reply through the Native Portal into the Host, checks provenance and frozen `PENDING_HUMAN_REVIEW` display, with **zero real OpenAI calls**.

## Known limitations / future Human Gate

- JSON validation does **not** prove the model's claims are true. Humans must compare advice to original evidence before accepting it.
- Requests can fail validation after billing. The app intentionally does not retry automatically; 600 output tokens may be insufficient for some real model responses.
- Session-only credentials do not survive app restart. Native per-process request counts do not prove lifetime charges; consult your provider billing.
- This is not an end-to-end human paid API UAT, not official LeetCode evaluation, not an employment score, and not E3-D's complete SMART training plan.
- Only approve a public GitHub commit after on-device native/WebKit and private-data checks. Keep generated `verification_*` output local until independently sanitized.
