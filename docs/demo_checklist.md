# Demo Checklist

Date: 2026-05-14

## Startup checklist
- [ ] Open terminal 1 for backend
- [ ] Open terminal 2 for frontend
- [ ] Seed demo database
- [ ] Run backend tests
- [ ] Start backend and verify health
- [ ] Build or run frontend
- [ ] Run 5 demo queries in order
- [ ] Verify response shows intent, route, confidence, warnings, disclaimer, evidence

## Seed command
```bash
cd backend
python scripts/seed_data.py
```

## Backend commands
```bash
cd backend
pytest -q
uvicorn app.main:app --reload
```

Health check:
```bash
curl http://127.0.0.1:8000/health
```

## Frontend commands
```bash
cd frontend
npm install
npm run dev
```

Build check:
```bash
cd frontend
npm run build
```

## Test command
```bash
cd backend
pytest -q
```

## Demo queries in order + expected result
1. `FPT niem yet o san nao?`
   Expected: intent `company_info`, route `direct`, answer states FPT listed on HOSE, DB evidence present.
2. `Gia FPT 3 thang gan day the nao?`
   Expected: intent `market_data`, route `direct`, answer includes 3-month return and start/latest close, DB evidence present.
3. `Tinh RSI14 va SMA20 cua FPT.`
   Expected: intent `technical_analysis`, route `analytics`, answer includes RSI14 and SMA20 (plus return), analytics evidence present.
4. `Tin tuc gan day ve HPG la tich cuc hay tieu cuc?`
   Expected: intent `news_sentiment`, route `rag`, answer states sentiment direction, news/report evidence snippets present.
5. `FPT co dang theo doi khong? Neu ly do va rui ro.`
   Expected: intent `investment_advisory`, route `advisory`, answer includes status + quantitative/qualitative reasons + risks, evidence present.

For all 5:
- confidence field present
- disclaimer present
- demo/mock warning visible

## Troubleshooting notes
- If backend says DB not ready: rerun `python scripts/seed_data.py`.
- If frontend cannot connect: verify backend is running on `http://127.0.0.1:8000`.
- If ticker missing error appears: use one of `FPT`, `HPG`, `VCB`, `VNM`.
- Empty or unknown query returns safe fallback with low confidence by design.
- If terminal shows Vietnamese garbled text, continue demo via UI (response contract still valid).
