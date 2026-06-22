# A.N.N. — System Architecture

> **Version:** 2.0
> **Last Updated:** 2026-06-22
> **Status:** Monolith → Microservice migration in progress

---

## Overview

A.N.N. is an autonomous AI news production platform. Raw news events enter from one end; fact-checked, multi-language broadcast scripts, AI anchor videos, and social media posts exit from the other — with zero human intervention.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          A.N.N. SYSTEM ARCHITECTURE                        │
│                                                                             │
│  DATA SOURCES ──► AI AGENT PIPELINE ──► CONTENT ENGINE ──► DISTRIBUTION    │
│                                                                             │
│  NewsAPI           Discovery            Article Gen       Website          │
│  GDELT             Fact Verify           Voice Gen         YouTube          │
│  AlphaVantage      Legal Check           Video Gen         Social Media     │
│  RSS Feeds         Script Write          Thumbnail Gen     Telegram         │
│  Gov Feeds         SEO Optimize                            WhatsApp         │
│  Social Signals    Translate                               RSS/Atom         │
│                    Produce Video                           WebSocket API    │
│                    Publish                                                   │
│                         │                                                   │
│                         ▼                                                   │
│                  ANALYTICS + FEEDBACK LOOP ──► AGENT LEARNING              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Frontend

### 1.1 Web Application (`frontend/web/`)

**Stack:** Next.js 16 · TypeScript · TailwindCSS

| Layer | Technology | Purpose |
|---|---|---|
| Framework | Next.js 16 (App Router) | SSR, routing, API proxying |
| Language | TypeScript | Type safety across components |
| Styling | TailwindCSS | Utility-first CSS, dark theme |
| State | Zustand | Client-side stores (dashboard, news, auth) |
| Data Fetching | React Query (`@tanstack/react-query`) | Server state, polling, cache invalidation |
| Animation | Framer Motion | Page transitions, micro-interactions |
| Charts | Recharts | Analytics dashboards (planned) |
| Forms | React Hook Form | Settings modal, article input, studio forms |
| Auth | Supabase Auth (via Zustand store) | Login, signup, password reset, session |

**Pages:**

```
/                   Dashboard — Pipeline control, stats, scripts, activity log
/news               Public news — Ticker, hero, category nav, feed grid, reader modal
/portal             Enterprise — Auth gate, sidebar, overview/API/social/studio tabs
```

**Key Architecture Decisions:**

- **No SSR for data** — All news data fetched client-side via React Query with polling intervals (5s health, 30s scripts). The backend is the source of truth.
- **Supabase Auth over Clerk** — Matches the existing backend auth. Auth state lives in a Zustand store (`auth-store.ts`), not in a provider wrapper.
- **API proxy via `next.config.ts`** — `/api/backend/*` rewrites to FastAPI, avoiding CORS in production.
- **Component colocation** — Each page has its own component directory (`components/dashboard/`, `components/news/`, `components/portal/`) rather than a flat components folder.

### 1.2 Legacy Frontend (`frontend/` root)

Vanilla HTML/CSS/JS served via Vercel. Three pages: `index.html` (dashboard), `public/news.html` (news reader), `public/portal.html` (B2B portal with inline Supabase SDK). Will be deprecated once `frontend/web/` reaches feature parity.

### 1.3 Mobile App (`frontend/mobile/`) — Planned

React Native / Expo. News reader, video playback, push notifications.

### 1.4 Admin Panel (`frontend/admin/`) — Planned

Internal ops dashboard. Content moderation, user management, agent monitoring.

---

## 2. Backend

### 2.1 Current: Monolith (`backend/`)

A single FastAPI application serving all API endpoints, running the AI pipeline, and managing B2B clients.

```
backend/
├── main.py              ← FastAPI app, all routes, lifespan, CORS, metrics
├── config.py            ← pydantic-settings, all env vars
├── celery_app.py        ← Celery worker configuration
│
├── agents/              ← AI processing (LLM calls)
│   ├── fact_extractor   ← Extract structured facts from raw text
│   ├── scriptwriter     ← Generate broadcast scripts from facts
│   ├── headline_gen     ← Create headlines from scripts
│   ├── translator       ← EN → HI translation
│   └── critic           ← Quality review and rewrite suggestions
│
├── ingestion/           ← Data source connectors
│   ├── base_source      ← Abstract base class for all sources
│   ├── newsapi_source   ← NewsAPI.org (80K+ sources)
│   ├── gdelt_source     ← GDELT global event database
│   └── alphavantage     ← Financial market data
│
├── media/               ← Content production APIs
│   ├── elevenlabs_tts   ← Voice synthesis (EN + HI clones)
│   └── heygen_video     ← Avatar video generation
│
├── services/
│   ├── pipeline         ← Orchestrates full agent pipeline
│   ├── tasks            ← Celery async task definitions
│   ├── queue_manager    ← Job tracking and progress
│   ├── auth             ← B2B API key verification (X-ANN-API-Key header)
│   ├── billing          ← Stripe checkout + webhook handling
│   ├── webhook          ← Outbound webhook delivery
│   └── supabase_client  ← Supabase DB client
│
├── social/              ← Platform-specific posters
│   ├── twitter_poster   ← Twitter/X API
│   ├── facebook_poster  ← Facebook Graph API
│   ├── instagram_poster ← Instagram Graph API
│   └── social_scheduler ← Timing and queue management
│
├── feeds/               ← Syndication
│   ├── rss_feed         ← RSS 2.0 XML generation
│   ├── atom_feed        ← Atom XML generation
│   └── embed_widget     ← Embeddable JS ticker widget
│
├── models/
│   ├── schemas          ← Pydantic models (ArticleInput, BroadcastScript, etc.)
│   └── b2b_database     ← SQLAlchemy models (ClientAPIKey)
│
├── utils/
│   ├── logger           ← structlog configuration
│   └── rate_limiter     ← Per-service RPM throttling
│
└── alembic/             ← Database migrations
```

**Runtime Architecture:**

```
                    ┌──────────────┐
                    │   Clients    │
                    │ (Web, API)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   FastAPI    │ :8000
                    │   (main.py) │
                    └──┬───┬───┬──┘
                       │   │   │
            ┌──────────┘   │   └──────────┐
            ▼              ▼              ▼
     ┌────────────┐ ┌───────────┐ ┌────────────┐
     │   Redis    │ │  Celery   │ │  Supabase  │
     │   Cache    │ │  Worker   │ │  Postgres  │
     │   :6379    │ │           │ │  (cloud)   │
     └────────────┘ └───────────┘ └────────────┘
                           │
                    ┌──────▼───────┐
                    │  External    │
                    │  APIs        │
                    │  (LLM, TTS,  │
                    │   HeyGen)    │
                    └──────────────┘
```

### 2.2 Target: Microservice Architecture

Each bounded context becomes an independently deployable service with its own database connection, Dockerfile, and health endpoint.

| Service | Port | Responsibility | Migrated From |
|---|---|---|---|
| **api-gateway** | 8000 | Routing, rate limiting, auth validation | `main.py` routes |
| **auth-service** | 8001 | Supabase Auth, JWT, RBAC, API key CRUD | `services/auth.py`, `models/b2b_database.py` |
| **article-service** | 8002 | Article CRUD, scripts, categories, feeds | `models/schemas.py`, `feeds/` |
| **video-service** | 8003 | TTS + avatar generation, media storage | `media/` |
| **analytics-service** | 8004 | Engagement tracking, metrics, agent scoring | New |
| **search-service** | 8005 | Full-text + vector search | New |
| **notification-service** | 8006 | Social posting, webhooks, push, email | `social/`, `services/webhook.py` |

**Inter-Service Communication:**

```
┌────────────┐     HTTP/gRPC     ┌─────────────────┐
│ API Gateway │ ◄──────────────► │ Auth Service     │
│   :8000     │                  │ Article Service  │
│             │                  │ Video Service    │
└──────┬──────┘                  │ Search Service   │
       │                         └────────┬────────┘
       │     Redis Streams / Pub-Sub      │
       └──────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │ Notification    │  (async, event-driven)
              │ Analytics       │
              └─────────────────┘
```

- **Sync calls** (API Gateway → Auth, Article, Search): REST or gRPC for request/response patterns
- **Async events** (new article published, video ready): Redis Streams for fan-out to Notification + Analytics services

---

## 3. AI Agents

### 3.1 Pipeline Architecture

The agent pipeline is a directed acyclic graph (DAG) where each agent receives structured input, performs a specialized task, and passes output downstream.

```
                    ┌─────────────────┐
                    │  Raw News Event  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Discovery Agent │  Ingest + dedup + relevance scoring
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Fact Agent     │  Claim extraction + cross-reference
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Legal Agent    │  Copyright, defamation, GDPR scan
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Rewrite Agent   │  Broadcast script generation
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Critic Agent   │  Quality review → rewrite loop
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Headline Agent  │  Click-worthy headline
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  SEO Agent      │  Keywords, meta tags, schema.org
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │Translation Agent│  EN → HI (extensible to more)
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Avatar Agent   │  ElevenLabs TTS + HeyGen video
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │Publishing Agent │  Web + social + API + webhooks
                    └─────────────────┘
```

### 3.2 Agent Implementation

**Current state** — agents are Python classes making OpenAI-compatible API calls:

```python
class ScriptwriterAgent:
    async def generate(self, facts: ExtractedFacts) -> str:
        response = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[system_prompt, user_prompt],
        )
        return response.choices[0].message.content
```

**Target state** — agents become autonomous units with:

| Capability | Implementation |
|---|---|
| Structured I/O | Pydantic models for input/output contracts |
| Memory | Per-agent persistent context (`ai/memory/`) |
| RAG | Vector retrieval for fact grounding (`ai/rag/`) |
| Orchestration | DAG-based pipeline with LangGraph or custom engine |
| Prompt management | Versioned prompts in `ai/prompts/` |
| Quality scoring | Critic agent scores → feedback loop → prompt tuning |

### 3.3 LLM Configuration

| Setting | Default | Options |
|---|---|---|
| `LLM_MODEL` | `gpt-4o` | Any OpenAI-compatible model |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Gemini: `https://generativelanguage.googleapis.com/v1beta/openai` |
| `LLM_RPM` | 10 | Rate limit (requests per minute) |

The system uses the OpenAI SDK with configurable `base_url`, making it compatible with any OpenAI-compatible provider (OpenAI, Google Gemini, Anthropic, local models via Ollama/vLLM).

---

## 4. Infrastructure

### 4.1 Local Development

```yaml
# docker-compose.yml
services:
  ann-backend:     # FastAPI app :8000
  redis:           # Cache + Celery broker :6379
  celery_worker:   # Async task processor
  prometheus:      # Metrics scraper :9090
  grafana:         # Dashboards :3000
```

Run: `docker-compose up --build`

### 4.2 Database

| Layer | Technology | Purpose |
|---|---|---|
| Primary DB | Supabase (managed Postgres) | User auth, B2B clients, article metadata |
| Local fallback | SQLite via aiosqlite | Development without Postgres |
| ORM | SQLAlchemy 2.0 (async) | Models, queries, connection pooling |
| Migrations | Alembic | Schema versioning |
| Cache | Redis | API response cache, Celery broker, rate limit state |

**Connection management:**

```python
# Postgres with connection pooling
engine = create_async_engine(DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### 4.3 Task Queue

```
┌──────────┐     Redis      ┌──────────────┐
│ FastAPI   │ ──── broker ──►│ Celery Worker │
│ (enqueue) │                │ (execute)     │
└──────────┘                 └──────────────┘
```

Heavy operations are offloaded to Celery workers:
- Full pipeline runs (ingest → script → translate → media)
- Audio/video generation (ElevenLabs, HeyGen — 10-60s per call)
- Social media posting (rate limited per platform)
- Webhook delivery (retries with exponential backoff)

### 4.4 Monitoring

| Component | Tool | Endpoint |
|---|---|---|
| Metrics | Prometheus + `prometheus-fastapi-instrumentator` | `/metrics` |
| Dashboards | Grafana | `:3000` |
| Logging | structlog (structured JSON) | stdout |
| Health | Custom endpoint | `/health` |

**Key metrics tracked:**
- Request latency (p50, p95, p99) per endpoint
- Active pipeline jobs and queue depth
- Error rates by service and endpoint
- External API call latency (LLM, TTS, HeyGen)

### 4.5 Production Deployment (Target)

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │API GW   │  │Auth Svc │  │Article  │  │Video    │  │
│  │(3 pods) │  │(2 pods) │  │(3 pods) │  │(2 pods) │  │
│  └────┬────┘  └─────────┘  └─────────┘  └─────────┘  │
│       │                                                 │
│  ┌────▼────┐  ┌─────────┐  ┌─────────┐               │
│  │Ingress  │  │Redis    │  │Postgres │               │
│  │(NGINX)  │  │Cluster  │  │(Supabase│               │
│  └─────────┘  └─────────┘  │ or RDS) │               │
│                             └─────────┘               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐               │
│  │Promethe │  │Grafana  │  │Celery   │               │
│  │us       │  │         │  │Workers  │               │
│  └─────────┘  └─────────┘  └─────────┘               │
└─────────────────────────────────────────────────────────┘
         │                          │
    ┌────▼────┐                ┌────▼────┐
    │   CDN   │                │ Vercel  │
    │(media)  │                │(frontend│
    └─────────┘                └─────────┘
```

**Provisioning:** Terraform (`infrastructure/terraform/`)
**Orchestration:** Kubernetes (`infrastructure/kubernetes/`)

---

## 5. Data Flow

### 5.1 News Pipeline (Happy Path)

```
1. TRIGGER
   Client hits POST /api/v1/pipeline/run
   or Celery cron fires scheduled ingestion

2. INGEST
   Discovery Agent calls NewsAPI/GDELT/AlphaVantage
   Raw articles deduplicated by semantic similarity
   Relevant articles scored and ranked

3. PROCESS (per article)
   FactExtractorAgent.extract(raw_text)
     → ExtractedFacts { claims[], entities[], sources[] }

   ScriptwriterAgent.generate(facts)
     → english_script (broadcast-ready text)

   CriticAgent.review(script)
     → score, rewrite suggestions
     → if score < threshold: loop back to Scriptwriter

   HeadlineGeneratorAgent.generate(script)
     → headline (click-optimized)

   TranslatorAgent.translate(script, target="hi")
     → hindi_script

4. PRODUCE (if generate_media=true)
   ElevenLabsTTS.generate(script, voice_id, language)
     → audio_url (.mp3)

   HeyGenVideoGenerator.generate(script, avatar_id)
     → video_url (.mp4)

5. STORE
   BroadcastScript saved to script_store (in-memory)
   Metadata persisted to Supabase/SQLite

6. DISTRIBUTE
   WebSocket push to /ws/breaking-news subscribers
   Social posters queue posts to Twitter/Facebook/Instagram
   RSS/Atom feeds regenerated
   B2B webhooks fired to registered endpoints

7. TRACK
   Analytics service records the generation event
   Engagement metrics collected post-distribution
   Agent performance scores updated
```

### 5.2 B2B API Flow

```
Client Request
    │
    ▼
API Gateway validates X-ANN-API-Key header
    │
    ▼
Auth Service checks key against DB
    ├── Invalid/expired → 401 Unauthorized
    ├── Quota exceeded → 429 Too Many Requests
    └── Valid → increment requests_used counter
            │
            ▼
      Route to Article Service
            │
            ▼
      Return JSON feed / WebSocket stream
```

### 5.3 B2B Checkout Flow

```
Client clicks "Purchase API Key"
    │
    ▼
POST /api/v1/b2b/checkout?tier=pro
    │
    ▼
Stripe Checkout Session created
    │
    ▼
Client redirected to Stripe payment page
    │
    ▼
Payment succeeds → Stripe fires webhook
    │
    ▼
POST /api/v1/webhooks/stripe
    │
    ▼
System generates ann_sk_* API key
Stores in ClientAPIKey table
Sets monthly_quota based on tier
    │
    ▼
Client receives API key via email/portal
```

---

## 6. Security

### 6.1 Authentication & Authorization

| Layer | Mechanism | Implementation |
|---|---|---|
| Portal Users | Supabase Auth (email/password) | GoTrue, JWT sessions |
| B2B API | API key in `X-ANN-API-Key` header | SQLAlchemy lookup + quota check |
| Admin Routes | `X-Admin-Token` header | Hardcoded token (to be migrated to RBAC) |
| Frontend | Supabase client SDK | Session persisted in browser |

### 6.2 API Security

| Control | Implementation |
|---|---|
| Rate Limiting | Per-service RPM limits via `utils/rate_limiter.py` |
| CORS | Configured in FastAPI middleware (currently `allow_origins=["*"]` — tighten for production) |
| Input Validation | Pydantic models for all request bodies |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| XSS | React (auto-escaped JSX), no `dangerouslySetInnerHTML` |
| Secrets | `.env` files excluded from git, Supabase anon key is public-safe |
| API Keys | `ann_sk_*` prefix, stored hashed (planned), blur-on-hover in UI |

### 6.3 External API Key Management

All external API keys stored in `backend/.env` and loaded via `pydantic-settings`:

```
LLM_API_KEY          → OpenAI / Gemini
NEWS_API_KEY         → NewsAPI.org
ELEVENLABS_API_KEY   → Voice synthesis
HEYGEN_API_KEY       → Video generation
STRIPE_SECRET_KEY    → Payment processing
TWITTER_BEARER_TOKEN → Social posting
FACEBOOK_PAGE_TOKEN  → Social posting
INSTAGRAM_ACCESS_TOKEN → Social posting
```

Admin can update keys at runtime via `POST /api/v1/admin/settings` (writes to `.env`).

### 6.4 Security Roadmap

- [ ] Hash B2B API keys at rest (store hash, compare on auth)
- [ ] Tighten CORS to specific origins
- [ ] Migrate admin auth from hardcoded token to RBAC
- [ ] Add request signing for inter-service calls
- [ ] SOC 2 Type II compliance audit
- [ ] Implement API key rotation with grace period
- [ ] Add audit logging for all admin operations

---

## 7. Scaling

### 7.1 Current Bottlenecks

| Bottleneck | Cause | Mitigation |
|---|---|---|
| LLM API calls | 10 RPM limit, 2-10s per call | Celery workers, request queuing, batch processing |
| Video generation | HeyGen: 30-60s per video, 5 RPM | Async queue, priority tiers, caching |
| In-memory script store | Data lost on restart | Migrate to Supabase/Postgres persistence |
| Single FastAPI process | CPU-bound during pipeline runs | Celery offloading, horizontal pod scaling |

### 7.2 Horizontal Scaling Strategy

```
                Load Balancer
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │FastAPI 1│ │FastAPI 2│ │FastAPI 3│   Stateless API pods
   └────┬────┘ └────┬────┘ └────┬────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
              ┌────────────┐
              │   Redis    │   Shared state (cache, sessions, queues)
              └────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Worker 1 │ │Worker 2 │ │Worker 3 │   Celery workers (scale by queue depth)
   └─────────┘ └─────────┘ └─────────┘
```

**Scaling rules:**
- API pods: scale on CPU > 70% or request latency p95 > 500ms
- Celery workers: scale on queue depth > 50 pending tasks
- Redis: cluster mode with read replicas for cache reads
- Postgres: read replicas for feed queries, primary for writes

### 7.3 Caching Strategy

| Layer | TTL | What's Cached |
|---|---|---|
| Redis (API responses) | 60s | `/feed/json`, `/feed/rss`, `/api/v1/scripts` |
| Redis (rate limits) | 60s | Per-service request counters |
| Browser (React Query) | 10s | `staleTime` for all queries |
| CDN (planned) | 5min | Static assets, generated media files |

### 7.4 Capacity Targets

| Metric | Current | Phase 3 Target | Phase 5 Target |
|---|---|---|---|
| API requests/sec | ~50 | 500 | 5,000 |
| Concurrent WebSocket connections | ~100 | 1,000 | 10,000 |
| Articles processed/hour | ~20 | 200 | 1,000 |
| Video generations/hour | ~5 | 50 | 200 |
| Database connections | 20 (pool) | 100 (cluster) | 500 (multi-region) |

---

## Appendix: Technology Decision Record

| Decision | Chosen | Alternatives Considered | Rationale |
|---|---|---|---|
| Backend framework | FastAPI | Django, Flask, Express | Async-native, auto OpenAPI docs, Pydantic integration |
| Frontend framework | Next.js | Remix, SvelteKit, Astro | React ecosystem, SSR/SSG flexibility, Vercel deployment |
| State management | Zustand | Redux, Jotai, Context | Minimal boilerplate, no providers, TypeScript-friendly |
| Auth provider | Supabase Auth | Clerk, Auth0, Firebase | Already using Supabase for DB, unified billing |
| Task queue | Celery + Redis | Bull (Node), Dramatiq, Temporal | Python-native, battle-tested, Redis as single dependency |
| Database | Supabase Postgres | PlanetScale, Neon, Firebase | Auth + DB + storage in one, generous free tier |
| LLM integration | OpenAI SDK (compatible) | LangChain, LlamaIndex | Direct API calls, no abstraction overhead, provider-agnostic via `base_url` |
| Monitoring | Prometheus + Grafana | Datadog, New Relic | Self-hosted, no per-host cost, Kubernetes-native |
| Video generation | HeyGen | Synthesia, D-ID | Best avatar quality, API-first, reasonable pricing |
| Voice synthesis | ElevenLabs | Google TTS, Amazon Polly | Voice cloning, multi-language, natural prosody |
