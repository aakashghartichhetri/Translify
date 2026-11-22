#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Docker Desktop / docker CLI is required.' >&2; exit 1; }
if ! docker info >/dev/null 2>&1; then
  echo 'Start Docker Desktop, then retry.' >&2; exit 1
fi
if [[ ! -f .env.demo ]]; then
  umask 077
  cat > .env.demo <<EOF
TRANSLIFY_DEMO_DB_PASSWORD=$(openssl rand -hex 24)
TRANSLIFY_DEMO_SECRET_KEY=$(openssl rand -hex 48)
EOF
  chmod 600 .env.demo
  echo 'Created local-only .env.demo secrets (not committed).'
fi
docker compose --env-file .env.demo -f docker-compose.demo.yml up --build -d
# Docker may return as soon as containers start, before the API begins serving.
# Wait for readiness so the next copy-and-paste smoke test is not racy.
ready=0
for attempt in {1..40}; do
  if curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [[ $ready -ne 1 ]]; then
  echo 'API did not become ready. Inspect Docker logs:' >&2
  echo '  docker compose --env-file .env.demo -f docker-compose.demo.yml logs --tail=100 api db demo_ai' >&2
  exit 1
fi
printf '\nLocal DEMO API READY: http://127.0.0.1:8000/docs\n'
printf 'These AI endpoints return demonstration placeholders, NOT real translations.\n'
printf 'Run: bash scripts/check-local-demo.sh\n'
printf 'Stop: bash scripts/stop-local-demo.sh\n'
