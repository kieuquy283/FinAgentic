#!/usr/bin/env bash
set -e
python scripts/seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
