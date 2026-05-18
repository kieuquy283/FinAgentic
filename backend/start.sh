#!/usr/bin/env bash
set -e

if [ -d backend ] && [ -f backend/app/main.py ]; then
  cd backend
fi

uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
