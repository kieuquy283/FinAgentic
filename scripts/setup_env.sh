#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Backend setup =="
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python backend/scripts/seed_data.py
python -m pytest -q backend/tests

echo "== Frontend setup =="
cd frontend
npm install
npm run build

echo "Setup completed successfully."
