#!/usr/bin/env bash
# Prepare real local commits in a FULL upstream checkout. No network actions.
# Usage: ./scripts/prepare_local_branches.sh /path/to/complete/Translify /path/to/extracted/overlay
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /path/to/Translify /path/to/overlay" >&2
  exit 2
fi
repo="$(cd "$1" && pwd)"
overlay="$(cd "$2" && pwd)"
expected='c2e648cdd6fc9ee67bb1e841c3b28e500f13d667'

[[ -d "$repo/.git" ]] || { echo 'Target must be a complete Git checkout.' >&2; exit 1; }
[[ -f "$overlay/server_core/app/routes.py" ]] || { echo 'Overlay missing backend code.' >&2; exit 1; }
[[ "$(git -C "$repo" rev-parse main)" == "$expected" ]] || {
  echo 'main has changed since the audited commit. Re-audit/rebase manually.' >&2; exit 1;
}
[[ -z "$(git -C "$repo" status --porcelain)" ]] || {
  echo 'Worktree is not clean. Stash/commit your work before proceeding.' >&2; exit 1;
}

copy_paths() {
  for file in "$@"; do
    mkdir -p "$repo/$(dirname "$file")"
    cp -p "$overlay/$file" "$repo/$file"
  done
}

begin_branch() {
  git -C "$repo" switch "$1"
  git -C "$repo" switch -c "$2"
}

finish_branch() {
  git -C "$repo" add -A
  git -C "$repo" commit -m "$1"
}

begin_branch main security/remove-tracked-secrets
copy_paths .gitignore server_core/.env.example server_core/.dockerignore
git -C "$repo" rm --cached --ignore-unmatch server_core/.env
finish_branch 'security: stop tracking environment configuration'

begin_branch security/remove-tracked-secrets security/backend-boundaries
copy_paths \
  server_core/app/config.py server_core/app/database.py server_core/app/auth_service.py \
  server_core/app/schemas.py server_core/app/upstream.py server_core/app/body_limit.py \
  server_core/app/translate_service.py server_core/app/routes.py server_core/app/main.py \
  server_core/app/init_db.py server_core/requirements.txt server_core/Dockerfile
finish_branch 'security: enforce authentication and upstream request boundaries'

begin_branch security/backend-boundaries security/processing-services
copy_paths \
  imageProcessing/Trocr.py imageProcessing/ocr.py imageProcessing/Dockerfile \
  speechProcessing/main.py speechProcessing/Dockerfile \
  translationEngine/main.py translationEngine/Dockerfile
git -C "$repo" rm --cached --ignore-unmatch imageProcessing/captured_frame.jpg
finish_branch 'security: isolate OCR and speech processing data'

begin_branch security/processing-services test/backend-integration
copy_paths \
  server_core/requirements-dev.txt server_core/tests/conftest.py \
  server_core/tests/test_api.py server_core/tests/test_processing_contracts.py
finish_branch 'test: verify security boundaries and service failures'

begin_branch test/backend-integration fix/flutter-user-workflows
while IFS= read -r -d '' file; do
  relative="${file#"$overlay/"}"
  copy_paths "$relative"
done < <(find "$overlay/translify/lib" "$overlay/translify/test" -type f -print0)
finish_branch 'fix: improve Flutter consent and translation workflows'

begin_branch fix/flutter-user-workflows ci/flutter-fastapi-verification
copy_paths .github/workflows/verify.yml
finish_branch 'ci: verify backend, Flutter, and dependency security'

begin_branch ci/flutter-fastapi-verification docs/readme-and-architecture
copy_paths README.md docs/apply-and-review.md docs/architecture.md docs/credential-response.md \
  docs/engineering-review.md docs/performance-validation.md \
  docs/prs/01-remove-tracked-secrets.md docs/prs/02-gateway.md \
  docs/prs/03-processing.md docs/prs/04-tests.md docs/prs/05-flutter.md \
  docs/prs/06-ci.md docs/prs/07-docs.md \
  scripts/prepare_local_branches.sh scripts/measure_translation_latency.py
finish_branch 'docs: explain architecture, test evidence, and team attribution'

printf '\nLocal-only stacked branches created. Nothing was pushed.\n'
git -C "$repo" branch --list
