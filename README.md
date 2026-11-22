# Translify 🌍

**Mobile text, camera, and speech translation | Collaborative capstone — Group 8**

Translify helps people understand signs, short messages, and spoken conversations across languages. A traveler reading a menu or two people sharing one phone should not have to copy text into several separate tools. The project joins a Flutter interface with Python services for recognition and translation. It is a capstone prototype, **not** a certified private, production-ready, or independently quality-validated translator.

## What it does

The following capabilities are implemented in the repository. Authentication, history boundaries, and translation API contracts are covered by mocked integration tests; real device and model demonstrations still require validation.

- **Accounts:** email registration, Argon2 password hashes, and expiring JWT access tokens.
- **Text translation:** English, Spanish, and French input submitted through the authenticated FastAPI endpoint and a Flutter screen.
- **Camera translation:** upload a JPEG or PNG, recognize text and bounding boxes with TrOCR, then translate recognized blocks.
- **Conversation translation:** record a speaker, transcribe WAV-compatible audio with faster-whisper, and translate the result.
- **Optional history:** saving is off by default and requested separately for each translation.
- **Account-scoped history:** view up to 50 recent entries or delete your own stored entries.

## Architecture

```text
Flutter mobile app (Dart)
        | HTTPS / JSON + multipart / bearer token
        v
FastAPI gateway (server_core) ----> PostgreSQL (SQLAlchemy)
        |
        +-- /capture -----------> TrOCR + OpenCV (imageProcessing)
        +-- /speech/transcribe -> faster-whisper (speechProcessing)
        +-- /translate --------> NLLB-200 via Transformers (translationEngine)
```

The gateway enforces authentication and history ownership. Image, audio, and translated text still travel between services; deployments must secure these network paths. The separate `docker-compose.yaml` references LibreTranslate, but the current Python translation endpoint uses **NLLB-200**, not LibreTranslate. Do not treat that Compose file as a complete application stack.

## Try it locally

Use Python 3.11, Flutter with Dart compatible with `translify/pubspec.yaml`, and PostgreSQL for a production-like setup. The following SQLite configuration is **development/test-only**; it is not a supported production database migration path.

```bash
cd server_core
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export DATABASE_URL=sqlite+pysqlite:///./translify-dev.db
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python -m app.init_db
PYTHONPATH=. pytest -q tests
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a separate terminal, from `translify/`:

```bash
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=TRANSLIFY_API_BASE=http://10.0.2.2:8000
```

`10.0.2.2` is for the Android emulator; physical devices require a reachable, secured endpoint. For actual OCR, speech, and translation, start the three model services and set their URLs using the variables in `server_core/.env.example`. For the self-contained local PostgreSQL + mocked-AI demonstration, see [local development](docs/local-development.md); it does not perform real AI. Consult [architecture](docs/architecture.md) for details. For source-code review and local branches, see [apply and review](docs/apply-and-review.md). Never expose a development HTTP endpoint on the public internet.

## Engineering and verification

The gateway restricts CORS, checks upload size and media signatures, validates upstream response shapes, bounds service timeouts, and returns sanitized errors. OCR no longer serves the last user's image; speech uses temporary, automatically cleaned files. The generated OCR snapshot is removed from tracking by the local branch-preparation script. The Flutter client uses secure token storage and displays understandable network failures. JWT logout does not revoke an already-issued token; access tokens expire on schedule.

**Locally verified:** 16 pytest tests passed against SQLite and controlled fake services, without paid APIs or model downloads. Python syntax compilation passed. **Not verified here:** clean dependency installation, PostgreSQL migrations, Flutter analysis/widget tests, Android builds, Docker startup, real-model latency, translation accuracy, or production traffic. CI workflows are provided but their results must be inspected after they run. No BLEU, COMET, or throughput claim is made.

## Limitations and ownership

Credentials previously committed to Git may require rotation; deleting a tracked file does not erase Git history. This project still needs migrations, rate limiting, stronger service-to-service authentication, real-device permission tests, accessibility review, performance measurements on reference hardware, and translation-quality evaluation on suitable datasets. Do not use it as the sole basis for medical, legal, or safety-critical decisions.

**Original capstone contributors:** Aakash Gharti Chhetri, Kelvin Capriel Reyes, Rusha Limbu, and Chin Tao Liu. Git commits and PRs remain the source for individual attribution; repository ownership does not imply sole authorship. The proposed hardening and test work is documented separately in [engineering notes](docs/engineering-review.md) so original team contributions remain visible.
