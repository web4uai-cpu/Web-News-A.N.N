---
name: run-backend
description: Start the A.N.N. FastAPI backend locally and smoke-test it. Use when asked to run, start, or verify the backend.
---

# Run the backend

```powershell
cd backend
pip install -r requirements.txt        # first time only
Copy-Item .env.example .env            # first time only, then fill keys
uvicorn main:app --reload --port 8000
```

Smoke test (in another terminal):
```powershell
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/scripts
```

Notes:
- Runs on SQLite (`backend/ann_enterprise.db`) unless `DATABASE_URL` is set; falls back to SQLite if remote Postgres is unreachable.
- Without `REDIS_URL`, pipelines run in-process via BackgroundTasks (no Celery needed).
- In `ENV=development` (default) pipeline/media endpoints allow unauthenticated calls; admin routes stay disabled until `ADMIN_SECRET` is set.
- Dev API key for B2B endpoints: `ann_demo_key_777` (dev-seeded only), header `X-ANN-API-Key`.
