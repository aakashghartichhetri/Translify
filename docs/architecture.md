# Translify architecture and operational boundaries

## Services and contracts

- **Flutter** uses `http` and `flutter_secure_storage` to call the API gateway. An expiring bearer token is included in authenticated requests. User-visible text, images, or audio are sent to the gateway when the user submits a translation. `TRANSLIFY_API_BASE` is a Flutter build-time setting; Android emulators use `10.0.2.2` for the host computer.
- **`server_core`** is a FastAPI gateway with SQLAlchemy models and PostgreSQL connection settings. Startup does not create database tables. Explicit schema bootstrapping (`python -m app.init_db`) is limited to development; production requires a reviewed schema migration and backup plan.
- **`translationEngine`** uses Hugging Face Transformers with the NLLB-200 distilled 600M model. It expects `{"text":"...","sourceLanguage":"en","targetLanguage":"es"}` and returns `{"translatedText":"..."}`. This is distinct from the unrelated LibreTranslate-only Compose example at the root.
- **`imageProcessing`** uses OpenCV plus TrOCR for recognition and returns `{"text":"...","contents":[{"text":"...","bbox":{...}}]}`. The gateway translates each recognized text block. No annotated source image is persisted or served by the current TrOCR API.
- **`speechProcessing`** uses faster-whisper for transcription, accepts multipart `file` and `language`, and returns `{"text":"...","language":"en"}`. Audio is written to a random temporary filename for the model and removed in a `finally` block.

The gateway uses HTTPX timeouts, response-shape validation, and sanitized 502/503/504 failures. Uploads have filename-independent media sniffing and image dimension checks. Full HTTP request buffering is capped to avoid unbounded multipart disk spooling, but parallel request counts must still be limited at ingress. Model workers serialize inference to limit simultaneous memory pressure. Backend health checks are liveness probes rather than guarantees that large models are preloaded or downstream calls will succeed.

## Authentication and privacy

Signup hashes passwords with Argon2. Login issues HS256 JWTs with subject, issue time, and expiration; signing keys must be strong secrets supplied at runtime. `/me`, `/translate`, and `/history` require valid bearer tokens and an active user. History reads and deletions use the authenticated user's database ID. `store_history` defaults to false, and an explicit true flag is necessary for each write. Existing saved entries remain after disabling future saves; `DELETE /history` removes the caller's entries.

**Important limitations:** Tokens are bearer credentials and cannot be individually revoked before their expiry without a revocation store. Preference storage is local to a device rather than a server-enforced account policy. Upstream services receive original recognized content; encryption, retention, legal consent, service-to-service authentication, and ingress ACLs depend on deployment controls not implemented in this repository. Database records are not currently encrypted by application-level code, and database backup retention is not managed here. Public exposure of model services must be prevented using private networking or authentication at the platform boundary.

## Failure handling and deployment

The gateway returns a generic error on upstream errors and database exceptions without exposing upstream bodies or SQL statements. The Flutter client maps known statuses and timeouts to short messages. OCR and speech are single-worker model implementations and may have cold-start latency. Do not deploy the development SQLite configuration. For PostgreSQL, configure a least-privilege application role and TLS/private network as supported by the provider, use a credential manager, and test schema migrations before rollout. Configure liveness/readiness checks, rate limits and concurrency at ingress, and a request/trace ID across services before using this beyond a controlled capstone demonstration.

The current `.env.example` contains placeholders only. Secret rotation, incident handling, history rewriting, production migrations, and deployment changes require explicit operator authorization. See [credential handling](credential-response.md) and [review](engineering-review.md).
