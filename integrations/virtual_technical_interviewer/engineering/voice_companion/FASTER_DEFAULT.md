# Faster voice default — 2026-10-24

Changed only the native initial rate and renderer fallback from 1.0 to 1.2 (Faster). Manual speed selection and all other behavior remain unchanged.

Command: `bash integrations/virtual_technical_interviewer/scripts/build_app.sh`

App rebuilt successfully. Build-time checks:

```text
Native tests: 133 passed, 0 failed; provider requests: 0
Provider tests: 69 passed, 0 failed; real provider requests: 0; transport: MOCK_HTTP
Voice tests: 100 passed, 0 failed; microphone captures: 0; synthesized audio: 0; provider requests: 0
```

No real audio or paid API calls. Physical listening UAT remains pending.
