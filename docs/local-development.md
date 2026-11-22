# Local development: full code checkout, demo stack, real models, and Git review

This guide uses the complete project created by `install.sh` in the downloaded setup package. The installer preserves original Git history and never pushes, merges or deploys code.

## Quick path: run the entire API with safe demonstration AI fixtures

**Requirements:** Docker Desktop running, Docker Compose v2, OpenSSL, and Python 3 on your Mac. Flutter SDK and Android emulator are needed only for the mobile UI. Running these demo services will download Docker images. The fixture service **does not perform actual translation, OCR, or speech recognition**; it exercises real FastAPI authentication, PostgreSQL, request/response contracts, network wiring, and history privacy boundaries. Never use outputs to judge language quality.

```bash
cd ~/Downloads/translify/Translify-Final
bash scripts/start-local-demo.sh
bash scripts/check-local-demo.sh
```

Expected result: `PASS: /health, signup, login, demo text translation and opted-in history`.

Open http://127.0.0.1:8000/docs to inspect the local gateway. Avoid posting personal data; the demo database stores any history you explicitly opt into. Stop services without deleting database volume:

```bash
bash scripts/stop-local-demo.sh
```

To remove stored demonstration data later, first back up anything important; only with explicit intent execute `docker compose --env-file .env.demo -f docker-compose.demo.yml down -v`.

## Flutter Android emulator

Install a Flutter version that includes Dart >=3.11.0 (see `translify/pubspec.yaml`) and Android tooling. Check:

```bash
flutter doctor -v
cd translify
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=TRANSLIFY_API_BASE=http://10.0.2.2:8000
```

`10.0.2.2` is the Android Emulator-to-host loopback alias; this project enables HTTP only in **debug Android** builds. On a physical Android device or for release, use a properly secured reachable HTTPS backend. For iOS, camera/microphone descriptions are present, but local HTTP and iOS builds have not been verified and may require local platform permissions.

## Backend unit/integration tests

Use Python 3.11, not a currently selected 3.15 shell alias; create a clean virtualenv:

```bash
cd ~/Downloads/translify/Translify-Final
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r server_core/requirements-dev.txt
PYTHONPATH=server_core python -m pytest -q server_core/tests
PYTHONPATH=. python -m pytest -q demo_ai/tests
```

The 16 gateway and processing tests use disposable SQLite and mocked HTTP, not the running Docker database. The 2 demo-fixture contract tests verify response shapes and disclaimers. Neither set proves the translation model's real-world accuracy, performance, deployment safety, or PostgreSQL migration correctness.

## Real AI (advanced, resource-heavy)

The actual model code is retained in `imageProcessing/Trocr.py`, `speechProcessing/main.py`, and `translationEngine/main.py`. The default OCR Dockerfile targets NVIDIA CUDA, which is generally **not appropriate for Docker Desktop on an Apple Silicon or Intel Mac**. Real-model operation requires platform-specific installation, compatible Torch/Transformers/Faster-Whisper dependencies, model downloads, and memory/compute capacity. The FastAPI gateway expects these internal service URLs:

```text
TRANSLATE_SERVICE=http://your-translation-host:port
IMAGE_TO_TEXT_SERVICE=http://your-ocr-host:port
SPEECH_TO_TEXT_SERVICE=http://your-speech-host:port
```

Do not advertise the demonstration fixture as real AI. Do not expose GPU services unauthenticated on public networks. See `docs/architecture.md` and `docs/performance-validation.md` before claiming full model integration or latency metrics.

## Push only after review

The installer also exports `Translify-Final-Source.zip` beside the checkout as a source-only snapshot. To publish changes with authentic attribution, push from the assembled Git checkout, not an extracted source snapshot. The installer produces a branch `improvement/translify-complete` based on your **real** upstream history and local feature/security branches underneath it. It changes **no** live repository and never pushes. After verifying the diff and required checks:

```bash
cd ~/Downloads/translify/Translify-Final
git status
git log --oneline main..improvement/translify-complete
git diff main...improvement/translify-complete --stat
git push -u origin improvement/translify-complete
```

Open a pull request targeting `main`. After your team's reviews, CI and permissions pass, merge **through GitHub**. Do not force-push `main`. `main` is never changed by these local setup commands. Before a public PR, assess any historically tracked `.env` for real credentials; deleting the file from the latest commit does not erase the old Git history.
