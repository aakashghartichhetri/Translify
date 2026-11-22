#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env.demo ]]; then
  docker compose --env-file .env.demo -f docker-compose.demo.yml down
else
  echo 'No .env.demo file found. Nothing stopped.'
fi
# No volumes deleted. Intentional data deletion requires a separate, explicit choice.
