# Cross-domain generation test: warehouse returns (not the original investment project)

**New unstructured Need**: “Returns cost too much. Make something that automatically checks items and helps our operators. We need it fast. Maybe an AI agent could talk to us.”

## Step 1 — Normalize without inventing a solution
Actor: return-desk worker [STAKEHOLDER_CLAIM, role presumed]. Trigger: returned parcel arrives [ASSUMPTION]. Friction: repeated classification/rework [ASSUMPTION]. Measurable baseline, daily volume, SKU/rules, loss and incident rate [UNKNOWN]. Desire: faster, auditable handling with fewer errors [STAKEHOLDER_CLAIM]. No vendor selected.

## Step 2 — Competing solution mechanisms
1. Manual SOP + rules spreadsheet; low build cost and known auditability.
2. Deterministic scan/validation app with warehouse system integration; core business rules fixed.
3. AI-assisted exception explanation and document classification behind explicit confidence and human approval.
Proceed to a pilot only after retrieving actual exception types, allowed data access and existing systems. Do not assume model inference is needed for barcode lookups.

## Step 3 — Convert abstract operators into a miniature PRD
- **FR-01 (PR07)**: Given a return item and an approved returns-policy version, the worker sees a structured disposition suggestion containing rule ID, evidence and timestamp. Invalid item IDs are rejected without updating stock.
- **FR-02 (PR05)**: Inventory change requires a verified staff role and active station permission. Denied cross-warehouse access must not leak item histories.
- **FR-03 (PR10)**: A low-confidence classification enters Needs Review; a human records a decision; agent may not independently dispose of goods.
- **NFR-01 (PR24)**: If warehouse API offline, preserve a pending transaction locally without falsely saying stock has been updated; reconciliation owner signs off.
- **DATA-01 (PR06)**: Item events, policy versions and dispositions each have owner, access scope, update cadence and retention policy.
- **ARCH-01 (PR09)**: Scan UI → deterministic rules/approval → authorized inventory API; LLM optional only for unstructured exception note interpretation.
- **VALUE-01 (PR14)**: Compare measured minutes/return and misclassification error rate for an agreed baseline cohort; do not assert dollar savings until rates and volume verified.
- **COST-01 (PR13)**: Person-days × actual rates + API fees + devices + security tests + support, with low/base/high cases.
- **AC-01 (PR15)**: Golden test returns valid item within threshold with cited policy; negative test invalid user blocked with no inventory write.
- **SCOPE-01 (PR03)**: First pilot one warehouse/one item category; company-wide rollout excluded until evidence and permission test pass.

## Step 4 — Output contract
Generate sections 00–31 of the master PRD only where relevant and mark others N/A, attach Need→FR→AC references and a supplier response sheet. Human Gate is PENDING until the warehouse lead reviews the pilot and limits.

## Reverse-generativity verdict
This new Need has no fund manager, securities, red/blue analyst team, Wind/Alpha API, historical investment budget, or three-class enterprise documents, yet the core structure still produces detailed product requirements. This is the core abstraction goal; it is an illustrative paper test, not a working deployed warehouse app.
