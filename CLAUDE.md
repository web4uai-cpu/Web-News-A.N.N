# A.N.N. — AI News Network

Fully automated AI-powered news platform: ingests news from multiple sources, processes through a multi-agent AI pipeline, produces articles/audio/video, distributes to web + social media.

## Tech Stack

- **Backend**: Python 3.13, FastAPI, Uvicorn (microservice architecture)
- **Frontend**: Next.js 16 + TypeScript + TailwindCSS in `frontend/web/`
  - State: Zustand | Data: React Query | Animation: Framer Motion
  - Charts: Recharts | Forms: React Hook Form | Auth: Supabase Auth
- **Frontend (legacy)**: Vanilla HTML/CSS/JS in `frontend/` root files
- **Queue**: Celery + Redis
- **Database**: Supabase (Postgres) + SQLAlchemy + Alembic, SQLite fallback
- **LLM**: OpenAI-compatible API (GPT-4o default, Gemini supported)
- **Media**: ElevenLabs TTS, HeyGen video avatars
- **Monitoring**: Prometheus + Grafana
- **Deploy**: Docker Compose, Kubernetes, Terraform (planned)

## Repo Structure (Microservice Architecture)

```
ANN/
├── frontend/
│   ├── web/                        # Next.js 16 app (main frontend)
│   │   ├── src/app/                # Pages: / (dashboard), /news, /portal
│   │   ├── src/components/         # dashboard/, news/, portal/, shared/, ui/
│   │   ├── src/lib/                # api.ts, store.ts, auth-store.ts, supabase.ts, utils.ts
│   │   └── next.config.ts
│   ├── mobile/                     # React Native app (planned)
│   ├── admin/                      # Internal admin panel (planned)
│   ├── index.html                  # Legacy vanilla dashboard
│   ├── css/ js/ public/            # Legacy vanilla assets
│
├── backend/
│   ├── main.py                     # Current monolith (FastAPI) — migration source
│   ├── config.py                   # pydantic-settings config
│   ├── api-gateway/                # Request routing, rate limiting, auth validation
│   ├── auth-service/               # Supabase Auth, JWT, RBAC, API key management
│   ├── article-service/            # Article CRUD, scripts, categories, feeds
│   ├── video-service/              # ElevenLabs TTS + HeyGen video generation
│   ├── analytics-service/          # User behavior, CTR, engagement, agent scoring
│   ├── search-service/             # Full-text + semantic search
│   ├── notification-service/       # Social posting, push, email, webhooks
│   ├── agents/ ingestion/ media/   # Current monolith modules (migration source)
│   ├── services/ social/ feeds/    # Current monolith modules (migration source)
│   └── models/ utils/ alembic/     # Current monolith modules (migration source)
│
├── agents/
│   ├── orchestrator/               # Master pipeline coordinator (DAG)
│   ├── discovery-agent/            # Source ingestion + deduplication
│   ├── fact-agent/                 # Fact verification + cross-referencing
│   ├── legal-agent/                # Legal compliance + content moderation
│   ├── rewrite-agent/              # Broadcast script generation
│   ├── seo-agent/                  # SEO optimization + metadata
│   ├── translation-agent/          # Multi-language translation (EN→HI+)
│   ├── avatar-agent/               # AI video production coordination
│   └── publishing-agent/           # Multi-channel content distribution
│
├── infrastructure/
│   ├── kubernetes/                 # K8s manifests for all services
│   ├── terraform/                  # Cloud IaC (VPC, clusters, DB, CDN)
│   ├── docker/                     # Multi-service compose files
│   └── monitoring/                 # Prometheus, Grafana, alerting
│
├── docs/
│   ├── architecture/               # System design, data flow diagrams
│   ├── api/                        # OpenAPI specs, SDK examples
│   ├── deployment/                 # Deploy guides, CI/CD, env vars
│   └── business/                   # PRD, pricing, monetization
│
├── ai/
│   ├── prompts/                    # System prompts per agent
│   ├── workflows/                  # Pipeline DAG definitions
│   ├── memory/                     # Agent long-term memory
│   └── rag/                        # Vector search, knowledge base
│
├── docker-compose.yml              # Current monolith stack
├── vercel.json                     # Frontend deployment
├── prometheus.yml                  # Metrics config
└── k8s/enterprise-stack.yaml       # Legacy K8s manifest
```

## Development Commands

```bash
# Backend (current monolith)
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000

# Celery worker
celery -A celery_app worker --loglevel=info

# Docker (full stack)
docker-compose up --build

# DB migrations
cd backend && alembic upgrade head

# Next.js Frontend
cd frontend/web
npm install
npm run dev                         # Dev server on port 3000
npm run build                       # Production build

# Tests
pytest backend/
```

## Architecture Pipeline

```
Data Sources (NewsAPI, GDELT, AlphaVantage, RSS, Gov feeds, Social signals)
    → Discovery Agent (ingestion + dedup)
    → Fact Agent (verification)
    → Legal Agent (compliance)
    → Rewrite Agent (script generation)
    → SEO Agent (optimization)
    → Translation Agent (EN → HI)
    → Avatar Agent (TTS + video)
    → Publishing Agent (web, social, mobile, Telegram, WhatsApp)
    → Analytics → Feedback Loop → Agent Learning
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Required keys:

| Variable | Service |
|---|---|
| `LLM_API_KEY` | OpenAI or Gemini |
| `NEWS_API_KEY` | NewsAPI.org |
| `ELEVENLABS_API_KEY` | Voice generation |
| `HEYGEN_API_KEY` | Video avatars |
| `ALPHA_VANTAGE_KEY` | Financial data |
| `TWITTER_BEARER_TOKEN` | Social posting |
| `FACEBOOK_PAGE_TOKEN` | Social posting |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |

## Conventions

- All config via `pydantic-settings` in `backend/config.py` — access with `get_settings()`
- Logging via `structlog` — use `get_logger()` from `backend/utils/logger.py`
- Rate limiting per external service via `backend/utils/rate_limiter.py`
- New ingestion sources extend `BaseSource` in `backend/ingestion/base_source.py`
- Async tasks go through Celery in `backend/services/tasks.py`
- Each new microservice gets its own `Dockerfile`, `requirements.txt`, and `README.md`
- API Gateway on port 8000, individual services on 8001-8006
- Frontend auth via Supabase Auth (Zustand store in `frontend/web/src/lib/auth-store.ts`)
