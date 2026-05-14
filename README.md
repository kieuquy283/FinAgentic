# Hybrid Agentic RAG MVP - Vietnamese Stock Assistant

## Purpose
This repository is a 4-day MVP demo of a Hybrid Agentic RAG architecture for Vietnamese stock analysis.

## Architecture Summary
- DB-first structured facts from SQLite (`companies`, `prices`, `news`, `reports`).
- Python-first deterministic analytics (SMA20, RSI14, return).
- Ingestion-first real market refresh into DB, then deterministic runtime reads from DB only.
- Rule-based routing to `direct`, `analytics`, `rag`, or `advisory` path.
- Evidence aggregation into typed `AnalyticalContext`.
- Guardrails always applied before final response.

## Backend Setup
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Explicit Environment Setup (recommended)

Windows PowerShell:
```powershell
.\scripts\setup_env.ps1
```

macOS/Linux:
```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

What these scripts do:
- create `.venv` at repo root (if missing)
- upgrade `pip`
- install `backend/requirements.txt`
- run `backend/scripts/seed_data.py`
- run backend tests (`pytest`)
- run `npm install` and `npm run build` in `frontend/`

Manual fallback (if script execution is blocked):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python backend\scripts\seed_data.py
python -m pytest -q backend\tests
cd frontend
npm install
npm run build
cd ..
```

If you are running inside a restricted sandbox and see errors like `No matching distribution found` (pip/network blocked) or `spawn EPERM` (node/esbuild process blocked), run the same commands above in a normal local terminal.

## Quick Demo Run (recommended)
```bash
cd backend
python scripts/seed_data.py
uvicorn app.main:app --reload
```

Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```

## Seed Database
```bash
cd backend
python scripts/seed_data.py
```

## Real Data Ingestion (DB refresh)
Run from `backend/` after environment setup:
```bash
python scripts/ingest_real_data.py --tickers FPT HPG VCB VNM
```

Required command targets:
```bash
python -m app.ingestion.market_ingestion
python -m app.ingestion.company_ingestion
```

Optional scoped runs:
```bash
python scripts/ingest_real_data.py --tickers FPT --prices-only
python scripts/ingest_real_data.py --tickers HPG --news-only
```

Notes:
- Runtime `/chat` does not call external APIs directly.
- Ingestion writes normalized data into DB tables, then services read from DB.
- `vnstock` is primary for prices/company/finance data.
- If real data is unavailable, guardrails show: `Real data missing; using demo fallback data.`

## Scheduled Refresh
- Windows Task Scheduler: run ingestion commands every 30-60 minutes for market/news and daily for company metadata.
- Linux/macOS cron example:
```bash
*/60 * * * * cd /path/to/repo/backend && . ../.venv/bin/activate && python -m app.ingestion.market_ingestion
```

## Run Tests
```bash
cd backend
pytest
```

## Run Backend
```bash
cd backend
uvicorn app.main:app --reload
```

## Run Frontend
```bash
cd frontend
npm install
npm run dev
```

Optional frontend env override:
```bash
cp frontend/.env.example frontend/.env
# set VITE_API_BASE_URL if backend is not on http://127.0.0.1:8000
```

## Deployment
- Render backend guide: `docs/deployment_render.md`
- Vercel frontend guide: `docs/deployment_vercel.md`

Render backend quick settings:
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `bash start.sh`
- Health Check Path: `/health`
- Env vars:
  - `PYTHON_VERSION=3.11.9`
  - `FRONTEND_ORIGINS=https://your-vercel-app.vercel.app`

## Demo Queries
Run in this order:
1. FPT niem yet o san nao?
2. Gia FPT 3 thang gan day the nao?
3. Tinh RSI14 va SMA20 cua FPT.
4. Tin tuc gan day ve HPG la tich cuc hay tieu cuc?
5. FPT co dang theo doi khong? Neu ly do va rui ro.

## Troubleshooting
- If `/chat` says data is not ready: run `cd backend && python scripts/seed_data.py` again.
- If real ingestion cannot fetch remote data, verify internet access and retry ingestion commands.
- If frontend cannot call backend: confirm backend is running at `http://127.0.0.1:8000`.
- If response says missing ticker: include one of `FPT`, `HPG`, `VCB`, `VNM`.
- Empty/unknown queries return safe fallback with low confidence by design.

## Expected DB Size
- Initial seeded DB: a few MB.
- After real ingestion (4 tickers, ~1 year OHLCV + raw/news/report snapshots): typically ~5-30 MB depending on refresh frequency.

## Ingestion Tables
- companies
- prices
- financial_ratios
- news
- raw_ingestion_items
- ingestion_logs
- source_metadata

## Limitations
- Uses deterministic mock data, not realtime exchange feeds.
- Rule-based intent routing only.
- Sentiment scoring is deterministic keyword-based.

## Disclaimer
Thong tin nay chi phuc vu muc dich tham khao va demo he thong, khong phai khuyen nghi dau tu ca nhan hoa. Nguoi dung can tu danh gia rui ro hoac tham khao chuyen gia tai chinh truoc khi ra quyet dinh.


