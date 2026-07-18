# A.N.N. — AI News Network

Fully automated AI-powered news platform: ingests news from multiple sources, processes through a multi-agent AI pipeline, produces articles/audio/video, distributes to web + social media.

## Architecture Reality (read this first)

- **The running backend is a modular monolith**: `backend/main.py` (FastAPI app factory) with domain routers in `backend/routers/`. It imports agents/ingestion/media/services directly. Its only live connections are Postgres, Redis, and external vendor APIs — verified at `/health` (liveness) and `/health/ready` (readiness).
- The per-service folders under `backend/` (`api-gateway/`, `auth-service/`, `article-service/`, `video-service/`, `analytics-service/`, `search-service/`, `notification-service/`) are **dormant future extraction targets** — implemented but NOT called by the monolith and NOT deployed (Railway runs only `ann-backend` + Postgres + Redis). See `backend/SERVICES.md`.
- **Postgres schema is Alembic-managed** — `init_db()` stamps/upgrades on startup. Change a model, then `alembic revision --autogenerate` + commit; never hand-write `ALTER TABLE`.
- The **real 9-node agent pipeline** is the LangGraph orchestrator in `agents/orchestrator/` (`graph.py`, `nodes.py`, `runner.py`), invoked via `POST /api/v1/pipeline/orchestrator`. The `agents/*-agent/` folders for discovery/legal/rewrite/seo/avatar/publishing are README-only stubs.
- The simple pipeline (`/api/v1/pipeline/run`) uses `backend/services/pipeline.py` + the small agents in `backend/agents/`.

## Tech Stack

- **Backend**: Python 3.13, FastAPI, Uvicorn — modular monolith
- **Frontend**: Next.js 16 + TypeScript + Tailwind v4 in `frontend/web/`
  - State: Zustand | Data: React Query | Animation: Framer Motion | Charts: Recharts | Forms: React Hook Form
- **Auth**: Firebase Auth on the frontend (`frontend/web/src/lib/auth-store.ts`); backend verifies Firebase ID tokens + B2B API keys + admin token via `backend/core/security.py`
- **Queue**: Celery + Redis (optional — BackgroundTasks fallback without REDIS_URL)
- **Database**: SQLAlchemy async; SQLite by default, Postgres via `DATABASE_URL` (Railway); Alembic present
- **LLM**: OpenAI-compatible API (GPT-4o default, Gemini supported)
- **Media**: ElevenLabs TTS, HeyGen video avatars
- **Deploy**: Backend on Railway, frontend on Vercel (root dir `frontend/web`); Docker Compose / K8s / Terraform in `infrastructure/`

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000

# Celery worker (only if REDIS_URL set)
celery -A celery_app worker --loglevel=info

# Next.js frontend
cd frontend/web
npm install
npm run dev          # port 3000
npm run build

# Tests / migrations
pytest backend/
cd backend && alembic upgrade head
```

## Security model (do not regress)

- `ADMIN_SECRET` has **no default** — admin routes return 503 until it is set. Never reintroduce a fallback token.
- Cost-sensitive endpoints (`/api/v1/ingest/*`, `/api/v1/pipeline/*`, `/api/v1/media/*`, `/api/v1/process_news`) require auth via `require_pipeline_access` (admin token, B2B key, or Firebase token). Open only in `ENV=development`.
- CORS comes from `CORS_ORIGINS` env (+ built-in `*.vercel.app` regex). Never `allow_origins=["*"]`.
- B2B API keys stored as SHA-256 hashes (`core/security.py:hash_api_key`); raw keys shown once at creation, listings masked.
- Demo key `ann_demo_key_777` exists only when `ENV=development`.
- Real secrets live only in `backend/.env` / `frontend/web/.env.local` (both gitignored). A `.claude` hook blocks secret-looking strings in tracked files.

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Key vars: `LLM_API_KEY`, `NEWS_API_KEY`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY`, `ALPHA_VANTAGE_KEY`, social tokens, plus security vars `ENV`, `ADMIN_SECRET`, `CORS_ORIGINS`, `FIREBASE_PROJECT_ID`. Frontend uses `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_FIREBASE_*`.

## Conventions

- Config via `pydantic-settings` in `backend/config.py` — access with `get_settings()`
- Auth dependencies from `backend/core/security.py` (`require_admin`, `require_pipeline_access`)
- Logging via `structlog` — `get_logger()` from `backend/utils/logger.py`
- Rate limiting per external service via `backend/utils/rate_limiter.py`
- New ingestion sources extend `BaseSource` in `backend/ingestion/base_source.py`
- Agent prompts are YAML in `ai/prompts/`, loaded via `ai/prompts/registry.py`
- Async tasks through Celery in `backend/services/tasks.py`
- Frontend API calls only through `frontend/web/src/lib/api.ts`; UI follows the dark glassmorphism tokens in `globals.css`

## Pipeline

```
Sources (NewsAPI, GDELT, AlphaVantage) → Discovery → Fact → Legal → Scriptwriter
  → Critic → Headline → SEO → Translation (EN→HI+) → Media (TTS/video) → Publishing
  (web /news, RSS/Atom/JSON feeds, social, B2B feed, WebSocket /ws/breaking-news)
```
