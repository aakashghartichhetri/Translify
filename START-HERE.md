# Translify — Run locally on a Mac

This directory contains a **complete** Translify source checkout: the original
capstone project plus the proposed Flutter, security, backend, test, CI and
engineering documentation improvements. The `main` branch and the original
clone remain unmodified. Everything is currently an **uncommitted change on
`improvement/translify-complete`**, so you can inspect and test it before deciding
to publish it. This is a candidate for review, not a production release.

## 1. Start Docker Desktop

Install and launch Docker Desktop for Mac. Wait for Docker to be running.

## 2. Run the local demonstration API

From the project root:

```bash
bash scripts/start-local-demo.sh
bash scripts/check-local-demo.sh
```

Open <http://127.0.0.1:8000/docs> in a browser. The local stack runs **real
FastAPI, JWT authentication and PostgreSQL**, with intentionally **fake AI
fixtures** that return labeled placeholder results. It exercises API flows but
DOES NOT actually translate, transcribe, or read images. Real model services
require separate resources and setup (see `docs/architecture.md`).

Stop it without removing your database data:

```bash
bash scripts/stop-local-demo.sh
```

## 3. Run the Flutter Android app

Install Flutter (with Dart 3.11+), Android Studio, the Android SDK and an
Android emulator. Open an Android emulator. In another terminal:

```bash
cd translify
flutter doctor -v
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=TRANSLIFY_API_BASE=http://10.0.2.2:8000
```

`10.0.2.2` is the Mac host address from the Android emulator. Keep Docker up.
The `http://` setting is only intended for Android **debug** mode; production
connections must use an authorized HTTPS endpoint. An iOS simulator requires
additional local HTTP configuration; this guide tests Android first.

## 4. Run backend tests independently (optional but recommended)

Install Python 3.11. From the repository root:

```bash
bash scripts/test-backend-local.sh
```

These tests do not download machine-learning models or use paid APIs.

## 5. Review locally before uploading anything

```bash
git status --short
git diff --stat
git diff --check
```

The project intentionally leaves the improvements **uncommitted** so the
installer does not need your Git identity. The full-source snapshot
`Translify-Final-Source.zip` is exported next to this folder. It is a source
snapshot without `.git`; use THIS Git folder for your PR.

## 6. When YOU decide to push a NEW branch only

Configure Git **with your own identity** in this repository:

```bash
git config user.name 'Your Real Name'
git config user.email 'your-github-email@example.com'
git add -A
git diff --cached --stat
git commit -m 'improvement: harden and test Translify application'
git push -u origin improvement/translify-complete
```

This pushes **only the new branch**, not `main`. Open a PR with base `main`,
compare `improvement/translify-complete`, review with the original contributors,
run GitHub Actions and merge only after explicit approval. Never force-push
`main`, and never share live secrets. Prefer splitting the combined proposal into
focused PRs after local review where feasible.

## Known limitations

Docker, Flutter and Android builds must be verified on your machine. The local
AI fixtures are not actual translations. Original Git history may contain
historically tracked secrets—evaluate rotation for any real active credentials.
PostgreSQL migration tooling, production rate limits, revocation, real-AI quality
and performance benchmarks are still outstanding. More in `docs/engineering-review.md`.
