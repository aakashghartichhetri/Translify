#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v python3.11 >/dev/null 2>&1; then py=python3.11; else
  echo 'Python 3.11 not found. On macOS with Homebrew run: brew install python@3.11' >&2
  exit 1
fi
"$py" -m venv .venv
source .venv/bin/activate
python -m pip install -r server_core/requirements-dev.txt
PYTHONPATH=server_core python -m pytest -q server_core/tests
PYTHONPATH=. python -m pytest -q demo_ai/tests
