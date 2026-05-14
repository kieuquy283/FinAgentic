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
- `QWEN_API_KEY=<your_key>`
- `QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- `QWEN_MODEL=qwen-plus`
- `REFRESH_TICKERS=FPT,HPG,VCB,VNM`
- `DAILY_REFRESH_ENABLED=true`
- `DAILY_REFRESH_HOUR=18`
- `DAILY_REFRESH_MINUTE=30`
- `APP_TIMEZONE=Asia/Ho_Chi_Minh`

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
- Internal APScheduler may not run reliably on free Render if service sleeps.
- Prefer one of:
  - Render Cron Job
  - GitHub Actions scheduled workflow
  - External cron hitting `POST /admin/refresh-data`
- CORS allows:
  - `http://localhost:5173`
  - `FRONTEND_ORIGIN` if set
  - comma-separated `FRONTEND_ORIGINS` if set
