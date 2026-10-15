# Roles, data classification and evidence contract

## Identity/permission matrix
| Role | Asset | Class | Action [read/search/upload/edit/export/share/delete] | Condition | Default | Required approval | Audit event | Denied test |
|---|---|---|---|---|---|---|---|---|

## Data inventory
| Data ID | Owner | Source | Schema/format | Purpose | Licence/right | Sensitivity | Freshness | Storage boundary | Ingestion validation | Deletion | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|

## AI and supplier boundary
| Dependency | Family [Model / Managed Agent / Embedded UI / Data API / Tool / Human / Infrastructure] | Credential controller | Permission scope | Required capabilities | Preflight | Fees | SLA | Retry/fallback | Status |
|---|---|---|---|---|---|---|---|---|---|---|

## Threat/negative tests
Unauthorized viewer; overshared output summary; secret in report/export; embedding leakage; missing citations; stale/incorrect source; prompt injection; expired token; vendor incident; deletion request. Each must have denial/repair/owner/evidence.
