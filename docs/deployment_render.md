# Render Backend Deployment

## Service settings
- Service type: `Web Service`
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `bash start.sh`
- Health check path: `/health`

## Required env vars
- `PYTHON_VERSION=3.11.9`
- `FRONTEND_ORIGINS=https://your-vercel-app.vercel.app`

Optional:
- `FRONTEND_ORIGIN=https://your-vercel-app.vercel.app`

## Start script
`backend/start.sh`:
```bash
#!/usr/bin/env bash
set -e
python scripts/seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Notes
- Runtime `/chat` reads local DB only.
- CORS allows:
  - `http://localhost:5173`
  - `FRONTEND_ORIGIN` if set
  - comma-separated `FRONTEND_ORIGINS` if set
