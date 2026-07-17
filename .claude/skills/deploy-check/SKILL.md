---
name: deploy-check
description: Pre-deploy checklist for Vercel (frontend) and Railway (backend). Use before deploying or when debugging a broken deployment.
---

# Deploy checklist

## Backend (Railway)
- `ENV=production` set — this makes pipeline/media endpoints require auth.
- `ADMIN_SECRET` set to a strong random value (admin routes are 503 without it).
- `CORS_ORIGINS` includes the production frontend domain (Vercel previews match the built-in `*.vercel.app` regex).
- `DATABASE_URL` (Postgres) and `REDIS_URL` present; `FIREBASE_PROJECT_ID` set for user-token verification.
- All provider keys present: LLM, NewsAPI, ElevenLabs, HeyGen, Stripe, social tokens.

## Frontend (Vercel)
- Root directory is `frontend/web` (root has no vercel.json by design; `frontend/web/vercel.json` holds headers/rewrites).
- `NEXT_PUBLIC_API_URL` points to the Railway backend.
- `NEXT_PUBLIC_FIREBASE_*` vars configured.
- `npm run build` passes locally before pushing.

## After deploy
- `GET {backend}/health` returns 200; dashboard loads over the API; `POST /api/v1/pipeline/run` without auth returns 401 in production.
- Guide: `docs/deployment/RAILWAY_VERCEL_SETUP.md`.
