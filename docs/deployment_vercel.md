# Vercel Frontend Deployment

## Project settings
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

## Required env vars
- `VITE_API_BASE_URL=https://your-render-service.onrender.com`
- `VITE_DEMO_MODE=false`

## Notes
- Frontend calls `${VITE_API_BASE_URL}/chat`.
- Local fallback when env is missing: `http://localhost:8000`.
