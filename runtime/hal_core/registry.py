"""Trusted adapter allowlist: reviewed with the HAL executable, never from imported archives."""
TRUSTED = {
  ('research-diagnostics','calculate-margin'): ('LOCAL_CALCULATE','trusted_adapters.research','run'),
  ('returns-operations','triage-return'): ('LOCAL_TRIAGE','trusted_adapters.returns','run'),
}
