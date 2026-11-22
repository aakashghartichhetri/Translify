# PR 2 — security: harden API authentication, uploads, CORS, and upstream failures

**Head:** `security/backend-boundaries`  
**Base:** `security/remove-tracked-secrets`

**Problem / evidence:** The gateway allowed wildcard CORS, logged SQL queries, parsed unbounded uploads, exposed raw upstream errors, and had minimal response validation. Database creation happened during application import.

**Solution / reasoning:** Require a strong configured HS256 signing secret and expiring JWT claims; reject inactive users; use explicit browser origin allowlists. Bound entire request bodies before multipart parsing, inspect image/audio bytes and dimension/duration where supported, and avoid filename trust. Validate HTTPX payloads with typed schemas, return sanitized upstream failures, disable SQL echo, add explicit schema initialization and user-scoped history deletion. Default history storage stays off.

**Tests:** Later `test/backend-integration` branch supplies 16 mocked pytest API/processing tests. Tests passed locally when applied as a combined overlay. No real PostgreSQL or model tests performed.

**Risks / follow-up:** New signup status is 201 (Flutter patch handles it); production requires an Alembic migration strategy, rate limits, token revocation and concurrent request controls. Larger model latency may exceed new timeouts; tune on measured hardware. No live credentials or data changed.
