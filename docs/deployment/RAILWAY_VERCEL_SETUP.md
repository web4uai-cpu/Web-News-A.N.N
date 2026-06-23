# A.N.N. Deployment Guide — Railway + Vercel

## Architecture Overview

```
                    ┌─────────────┐
                    │   Vercel     │
                    │  (Frontend)  │
                    │  Next.js 16  │
                    └──────┬──────┘
                           │ HTTPS
                           ▼
┌──────────────────────────────────────────────────────┐
│                 Railway Project                       │
│                                                      │
│  ┌──────────────┐     ┌──────────────┐              │
│  │ API Gateway   │────▶│ Auth Service │              │
│  │ :8000 (public)│     │ :8001        │              │
│  └──────┬───────┘     └──────────────┘              │
│         │                                            │
│  ┌──────┼──────────────────────────────────┐        │
│  │      ▼              ▼           ▼       │        │
│  │ Article:8002  Video:8003  Search:8006   │        │
│  │ Notify:8004   Analytics:8005            │        │
│  └─────────────────────────────────────────┘        │
│         │              │                             │
│  ┌──────▼──────┐ ┌─────▼─────┐                     │
│  │ PostgreSQL  │ │   Redis    │                     │
│  │  (plugin)   │ │  (plugin)  │                     │
│  └─────────────┘ └───────────┘                     │
│                                                      │
│  External: Supabase Auth, OpenAI, ElevenLabs, HeyGen │
└──────────────────────────────────────────────────────┘
```

---

## Step 1: Railway Project Setup

### 1.1 Create Railway Project

1. Go to [railway.app](https://railway.app) → **New Project** → **Empty Project**
2. Name it: `ann-production`

### 1.2 Add PostgreSQL

1. Click **+ New** → **Database** → **PostgreSQL**
2. Railway auto-provisions and injects `DATABASE_URL`
3. After creation, click the Postgres service → **Connect** tab → note:
   - `DATABASE_URL` (internal, for services)
   - `DATABASE_PUBLIC_URL` (external, for migrations from your machine)

### 1.3 Add Redis

1. Click **+ New** → **Database** → **Redis**
2. Railway auto-injects `REDIS_URL`
3. Note the internal URL: `redis://default:PASSWORD@redis.railway.internal:6379`

### 1.4 Set Shared Variables

Go to **Settings** → **Shared Variables** and add:

| Variable | Value | Used By |
|----------|-------|---------|
| `LLM_API_KEY` | `sk-...` | All agents |
| `LLM_MODEL` | `gpt-4o` | All agents |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | All agents |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Auth, Article |
| `SUPABASE_KEY` | Service role key | Auth, Article |
| `NEWS_API_KEY` | Your NewsAPI key | Discovery agent |
| `ELEVENLABS_API_KEY` | Your key | Video service |
| `HEYGEN_API_KEY` | Your key | Video service |

---

## Step 2: Deploy Backend Services

### 2.1 API Gateway (Public-Facing)

1. **+ New** → **GitHub Repo** → select `Web-News-A.N.N-1`
2. **Settings**:
   - Root Directory: `backend/api-gateway`
   - Builder: Dockerfile
3. **Variables** (add these):

```env
PORT=8000
WORKERS=2
LOG_LEVEL=info
CORS_ORIGINS=https://your-vercel-domain.vercel.app

# Internal service URLs (Railway private network)
AUTH_SERVICE_URL=http://ann-auth-service.railway.internal:8001
ARTICLE_SERVICE_URL=http://ann-article-service.railway.internal:8002
VIDEO_SERVICE_URL=http://ann-video-service.railway.internal:8003
NOTIFICATION_SERVICE_URL=http://ann-notification-service.railway.internal:8004
ANALYTICS_SERVICE_URL=http://ann-analytics-service.railway.internal:8005
SEARCH_SERVICE_URL=http://ann-search-service.railway.internal:8006
```

4. **Networking** → **Generate Domain** → note the public URL: `ann-api-gateway-production.up.railway.app`
5. (Optional) Add custom domain: `api.yourdomain.com`

### 2.2 Auth Service

1. **+ New** → **GitHub Repo** → same repo
2. **Settings**: Root Directory: `backend/auth-service`
3. **Variables**:

```env
PORT=8001
WORKERS=2
```

4. Link: **+ Variable Reference** → `${{Postgres.DATABASE_URL}}` and `${{Redis.REDIS_URL}}`
5. **Networking**: Service name = `ann-auth-service` (for internal DNS)

### 2.3 Article Service

Same pattern — Root: `backend/article-service`, PORT=8002, link Postgres + Redis.

### 2.4 Video Service

Root: `backend/video-service`, PORT=8003, link Postgres + Redis.
Add ElevenLabs/HeyGen keys as service-specific variables.

### 2.5 Notification Service

Root: `backend/notification-service`, PORT=8004, link Redis.
Add social media tokens as service-specific variables.

### 2.6 Analytics Service

Root: `backend/analytics-service`, PORT=8005, link Postgres + Redis.

### 2.7 Search Service

Root: `backend/search-service`, PORT=8006, link Postgres.
Add `LLM_API_KEY` for embedding generation.

### Service Name Convention

**IMPORTANT:** Railway internal networking uses service names. When creating each service, set the service name in **Settings → Service Name**:

| Service | Railway Service Name | Internal URL |
|---------|---------------------|--------------|
| API Gateway | `ann-api-gateway` | `ann-api-gateway.railway.internal:8000` |
| Auth | `ann-auth-service` | `ann-auth-service.railway.internal:8001` |
| Article | `ann-article-service` | `ann-article-service.railway.internal:8002` |
| Video | `ann-video-service` | `ann-video-service.railway.internal:8003` |
| Notification | `ann-notification-service` | `ann-notification-service.railway.internal:8004` |
| Analytics | `ann-analytics-service` | `ann-analytics-service.railway.internal:8005` |
| Search | `ann-search-service` | `ann-search-service.railway.internal:8006` |

---

## Step 3: Database Migrations

### Run from your machine:

```bash
# Get the PUBLIC database URL from Railway Dashboard → Postgres → Connect
export DATABASE_URL="postgresql://postgres:PASSWORD@HOST:PORT/railway"

cd backend
alembic upgrade head
```

### Or run from Railway CLI:

```bash
railway login
railway link  # select your project
railway run -- alembic -c backend/database/alembic_railway.ini upgrade head
```

---

## Step 4: Vercel Frontend Deployment

### 4.1 Import Project

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import GitHub repo: `Web-News-A.N.N-1`
3. **Framework Preset**: Next.js
4. **Root Directory**: `frontend/web`
5. **Build Command**: `npm run build`
6. **Output Directory**: `.next`

### 4.2 Environment Variables

Add in **Vercel Dashboard → Settings → Environment Variables**:

| Variable | Value | Environment |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://ann-api-gateway-production.up.railway.app` | Production |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxx.supabase.co` | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | All |
| `NEXT_PUBLIC_ENABLE_ADS` | `false` | All |
| `NEXT_PUBLIC_ENABLE_PREMIUM` | `false` | All |

### 4.3 Custom Domain (Optional)

1. **Settings** → **Domains** → Add `www.yourdomain.com`
2. Add CNAME record: `www` → `cname.vercel-dns.com`
3. Add A record: `@` → `76.76.21.21`

### 4.4 Update API Gateway CORS

After getting your Vercel domain, update the API Gateway's `CORS_ORIGINS`:

```
CORS_ORIGINS=https://your-project.vercel.app,https://www.yourdomain.com
```

---

## Step 5: Verify Deployment

### Health Checks

```bash
# API Gateway
curl https://ann-api-gateway-production.up.railway.app/health

# Individual services (through gateway)
curl https://ann-api-gateway-production.up.railway.app/api/v1/scripts/latest

# Frontend
curl https://your-project.vercel.app
```

### Expected `/health` Response:

```json
{
  "status": "healthy",
  "uptime_seconds": 1234,
  "services": {
    "auth": "connected",
    "article": "connected",
    "video": "connected",
    "database": "connected",
    "redis": "connected"
  }
}
```

---

## Railway Variable References (Linking)

Railway supports variable references across services. Instead of copy-pasting, use:

```
${{Postgres.DATABASE_URL}}     → auto-resolves to PostgreSQL connection string
${{Redis.REDIS_URL}}           → auto-resolves to Redis connection string
${{ann-api-gateway.RAILWAY_PUBLIC_DOMAIN}} → gateway's public domain
```

Set these via: **Service → Variables → + Variable Reference**

---

## Cost Estimates

### Railway (Hobby Plan — $5/month)

| Resource | Estimated Cost |
|----------|---------------|
| API Gateway | ~$3/mo |
| Auth Service | ~$2/mo |
| Article Service | ~$2/mo |
| Video Service | ~$3/mo |
| Notification Service | ~$2/mo |
| Analytics Service | ~$2/mo |
| Search Service | ~$2/mo |
| PostgreSQL | ~$5/mo |
| Redis | ~$3/mo |
| **Total** | **~$24/mo** |

### Railway (Pro Plan — $20/month)

Higher resource limits. Recommended for production.

### Vercel (Hobby — Free)

- 100GB bandwidth/month
- Serverless Functions
- Edge Network

### Vercel (Pro — $20/month)

- 1TB bandwidth
- Analytics
- Custom headers

---

## Troubleshooting

### Service can't connect to another service

- Verify service names match the internal URLs exactly
- All services must be in the same Railway project
- Check that the target service is running and healthy

### Database connection refused

- Ensure `DATABASE_URL` is linked via Railway variable reference, not hardcoded
- Check pool size isn't exceeding Railway's connection limits (default: 20)
- Use `DB_POOL_SIZE=5` and `DB_MAX_OVERFLOW=10` for Railway Hobby

### Vercel build fails

- Check that `Root Directory` is set to `frontend/web`
- Ensure `NEXT_PUBLIC_API_URL` is set (build-time variable)
- Check Node.js version compatibility (use 22.x)

### CORS errors

- Update `CORS_ORIGINS` in API Gateway to include your Vercel domain
- Include both `https://your-project.vercel.app` AND custom domain if applicable
- Redeploy the API Gateway after changing CORS

### Railway deploy stuck

- Check build logs for errors
- Verify Dockerfile path is correct in railway.toml
- Ensure `requirements.txt` exists in the service directory
