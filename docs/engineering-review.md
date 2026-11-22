# Translify technical review — evidence and boundaries

Baseline: upstream `main` at `c2e648cdd6fc9ee67bb1e841c3b28e500f13d667` (2026-05-18). This is a **proposed local overlay**, not merged code. The environment could read files via the GitHub connector but could not clone the repository over the network. Only changed/necessary files are packaged; all other upstream files remain unchanged when the overlay is applied to a complete checkout.

## Confirmed findings and proposed mitigations

| Risk | Evidence in baseline | Patch and residual risk |
| --- | --- | --- |
| P0: historical environment values | `server_core/.env` tracked at HEAD | Ignore + example + local deindex script; review/rotate any live exposed credentials, historical commits remain |
| P1: wildcard browser CORS | `server_core/app/main.py` used `allow_origins=["*"]` with credentials | Explicit CORS allowlist, credentials disabled; ingress remains deployment-owned |
| P1: unbounded multipart requests | `routes.py` used `await image.read()` and `await recording.read()` | Bounded ASGI request buffering plus per-file limits and real media inspection; ingress still needs concurrent request limits |
| P1: OCR image disclosure | `imageProcessing/Trocr.py` saved `captured_frame.jpg`, served `/captured_image`, and logged decoded text | Current OCR service no longer persists, serves, or logs those contents; local script de-indexes the tracked generated snapshot; remove previously generated snapshots during authorized operations |
| P1: speech path injection / retention | `speechProcessing/main.py` built a file path from client filename and deleted only after successful inference | Random temporary paths with unconditional cleanup and MIME signature checks |
| P1: unsafe error disclosures | routes and services included upstream response body / raw exceptions in API error responses | Sanitized API errors, typed response validation and constrained upstream timeouts; comprehensive monitoring still required |
| P1: SQL value logging | `database.py` configured SQLAlchemy `echo=True` | Disabled SQL echo and sensitive-content logging |
| P2: preference default issue | Flutter privacy screen checked only `"null"`/`"False"`, while storage could now return other values | Normalize true/false, start off, clear per-session preference on logout, add own-history deletion |
| P2: broken signup navigation | Flutter signup view referenced `context.pop` without calling it | Execute navigation after 201 success and show feedback |
| P2: starter widget test | `translify/test/widget_test.dart` asserted counter UI absent from Translify | Replace with text flow tests, add API/service/permission tests |
| P2: inaccurate architecture documentation | Root README described LibreTranslate, while `translationEngine/main.py` loads NLLB | README describes actual NLLB flow and notes Compose mismatch |

## Checks actually executed in the local overlay

`python -m compileall -q ...` completed for modified Python files. From `server_core`, `PYTHONPATH=. pytest -q --disable-warnings --maxfail=1` passed **16 tests** using a disposable SQLite database and HTTPX mocks. This checks registration, login, expired/missing tokens, authorization, isolation, opt-in/out and deletion, invalid content and size, empty transcripts, unavailable OCR/speech, translation timeouts, sanitized database errors, and model-free API contracts for all three processing services. Neither large model weights nor paid external APIs were loaded. Real OCR/Whisper/NLLB accuracy was not evaluated.

`flutter analyze`, `flutter test`, Flutter builds, actual PostgreSQL connections, Docker builds, clean dependency installs, GitHub Actions, full system e2e, and live hardware permission prompts **were not executed in this environment**. Do not treat CI configuration as evidence CI has passed. No latency or translation-quality measurements against real models have been made.

## Outstanding engineering work

No version-locked dependency hashes or automated Alembic migration baseline have been supplied. Auth rate limiting, forced token revocation, refresh tokens, deletion retention in DB backups, account-level consent synchronization, reverse-proxy quotas, model service ingress controls, distributed traces, runtime vulnerability scanning, accessibility evaluation, mobile platform testing, and real workload benchmarking remain open. The current test setup uses SQLite; PostgreSQL transaction semantics, concurrency, and schema compatibility need separate testing. Review the old git history privately for secrets before publishing patches or CI artifacts.

## Attribution

Original capstone names in repository documentation: **Aakash Gharti Chhetri, Kelvin Capriel Reyes, Rusha Limbu, Chin Tao Liu**. The visible commit history includes all four names; for example Kelvin Capriel Reyes' May 18 commit records history preference work, while Aakash Gharti Chhetri's May 12 commits update API routes. These examples do not establish sole ownership of any component. Contributions from the hardening overlay must be credited separately; no reviews, approvals, or GitHub PRs have been fabricated. Authorship/ownership should be confirmed with the team using git blame and accepted PRs.
