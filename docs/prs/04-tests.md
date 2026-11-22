# PR 4 — test: cover authentication, isolation and model-service failures

**Head:** `test/backend-integration`  
**Base:** `security/processing-services`

**Problem / evidence:** No Python integration tests were present in the inspected repository; the Flutter widget test still asserted the starter counter.

**Solution / reasoning:** Add pytest fixtures with a disposable SQLite database and HTTPX mock transports, so core behavior is reproducible without a running PostgreSQL server, paid services, model weights or cloud credentials. Use model-free endpoint tests for OCR, Whisper and NLLB API contracts.

**Tests:** `PYTHONPATH=. pytest -q --disable-warnings --maxfail=1` from `server_core` returned **16 passed, 17 warnings** in the local overlay. Python compileall passed. The test suite includes invalid/expired tokens, unauthorized routes, user history isolation, opt-in/out and deletion, malformed/oversized files, empty transcription, upstream unavailability/timeout, and safe database errors.

**Risks / follow-up:** SQLite does not test production PostgreSQL locking, transaction semantics or migration behavior. Real-model outputs and mobile end-to-end workflows are not covered.
