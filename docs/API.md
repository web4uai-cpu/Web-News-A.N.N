# A.N.N. — API Reference

> **Base URL:** `http://localhost:8000`
> **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)
> **Version:** 1.0

---

## Authentication

A.N.N. uses three authentication mechanisms depending on the endpoint:

| Method | Header | Used For |
|---|---|---|
| **Supabase Auth** | JWT Bearer token (browser session) | Portal UI login/signup |
| **B2B API Key** | `X-ANN-API-Key: ann_sk_*` | Commercial API access |
| **Admin Token** | `X-Admin-Token: <secret>` | Admin operations |

---

### POST `/api/v1/b2b/checkout`

Create a Stripe checkout session to purchase a B2B API key subscription.

**Auth:** None (public)

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `tier` | string | `pro` | Plan tier: `standard`, `pro`, `enterprise` |
| `client_name` | string | *required* | Company or developer name |
| `currency` | string | `usd` | Currency: `usd` or `inr` |

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

**Tier Quotas:**

| Tier | Monthly Requests | Price (USD) | Price (INR) |
|---|---|---|---|
| Standard | 5,000 | $49 | ₹3,999 |
| Pro | 25,000 | $199 | ₹14,999 |
| Enterprise | 100,000 | $499 | ₹39,999 |

---

### POST `/api/v1/webhooks/stripe`

Stripe webhook receiver. Auto-provisions API keys upon successful payment.

**Auth:** Stripe signature verification (`stripe-signature` header)

**Note:** Configure this URL in your Stripe Dashboard → Webhooks.

---

### POST `/api/v1/admin/clients`

Create a new B2B client and generate an API key.

**Auth:** `X-Admin-Token` header

**Request Body:**
```json
{
  "client_name": "Demo Corp",
  "plan_tier": "enterprise",
  "monthly_quota": 100000,
  "webhook_url": "https://example.com/webhook"
}
```

**Response:**
```json
{
  "message": "B2B Client Created Successfully",
  "client_name": "Demo Corp",
  "api_key": "ann_enterprise_a1b2c3d4e5f6",
  "monthly_quota": 100000,
  "webhook_url": "https://example.com/webhook"
}
```

---

### GET `/api/v1/admin/clients`

List all B2B clients with quota usage.

**Auth:** `X-Admin-Token` header

**Response:**
```json
[
  {
    "id": 1,
    "client_name": "Demo Corp",
    "api_key": "ann_enterprise_a1b2c3d4e5f6",
    "plan_tier": "enterprise",
    "quota": "1250/100000",
    "webhook_url": "https://example.com/webhook",
    "active": true
  }
]
```

---

## Articles

### POST `/api/v1/process_news`

Process a single raw article through the full AI editorial pipeline.

**Auth:** None

**Pipeline:** Fact Extraction → Script Writing → Critic Review → Headline → Translation

**Request Body:**
```json
{
  "source_url": "https://example.com/article",
  "raw_text": "Full article text here (minimum 50 characters)...",
  "source_name": "Example News",
  "category": "technology"
}
```

**Category Values:** `general`, `business`, `technology`, `science`, `health`, `sports`, `entertainment`, `politics`, `finance`, `geopolitics`

**Response:** [BroadcastScript](#broadcastscript)

```json
{
  "id": "a1b2c3d4",
  "headline": "AI Revolution Reshapes Global Markets",
  "english_script": "Good evening. In a dramatic turn of events...",
  "hindi_script": "शुभ संध्या। एक नाटकीय मोड़ में...",
  "category": "technology",
  "source_url": "https://example.com/article",
  "word_count_en": 245,
  "word_count_hi": 198,
  "estimated_duration_seconds": 98,
  "created_at": "2026-06-22T14:30:00Z"
}
```

---

### GET `/api/v1/scripts`

List all generated broadcast scripts, newest first.

**Auth:** None

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 20 | Max results (1–100) |

**Response:** Array of [BroadcastScript](#broadcastscript)

---

### GET `/api/v1/scripts/latest`

Get latest headlines for the breaking news ticker (lightweight response).

**Auth:** None

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 10 | Max results (1–30) |

**Response:**
```json
[
  {
    "id": "a1b2c3d4",
    "headline": "AI Revolution Reshapes Global Markets",
    "category": "technology",
    "created_at": "2026-06-22T14:30:00Z"
  }
]
```

---

### GET `/api/v1/scripts/{script_id}`

Get a single script by ID.

**Auth:** None

**Response:** [BroadcastScript](#broadcastscript) or `404`

---

### POST `/api/v1/ingest/newsapi`

Fetch articles from NewsAPI.org and process through the pipeline.

**Auth:** None (requires `NEWS_API_KEY` configured server-side)

**Request Body:**
```json
{
  "category": "technology",
  "query": "artificial intelligence",
  "max_articles": 5
}
```

**Response:** Array of [BroadcastScript](#broadcastscript)

---

### POST `/api/v1/ingest/financial`

Fetch financial news for specific stock tickers from Alpha Vantage.

**Auth:** None (requires `ALPHA_VANTAGE_KEY` configured server-side)

**Request Body:**
```json
{
  "symbols": ["AAPL", "NVDA", "MSFT"],
  "max_articles": 5
}
```

**Response:** Array of [BroadcastScript](#broadcastscript)

---

### POST `/api/v1/ingest/gdelt`

Fetch geopolitical events from the GDELT global event database.

**Auth:** None

**Request Body:**
```json
{
  "category": "geopolitics",
  "query": "UN summit",
  "max_articles": 5
}
```

**Response:** Array of [BroadcastScript](#broadcastscript)

---

### GET `/api/v1/b2b/feed/json`

Premium commercial JSON feed for B2B API clients.

**Auth:** `X-ANN-API-Key` header (required)

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `category` | string | *all* | Filter by category |
| `limit` | integer | 20 | Max results (1–50) |

**Response:** Same as `/feed/json` but metered against client quota.

**Error Responses:**

| Code | Reason |
|---|---|
| `401` | Missing or invalid API key |
| `429` | Monthly quota exceeded |

---

## Videos

### POST `/api/v1/media/generate_audio`

Generate TTS audio for a script using ElevenLabs voice clones.

**Auth:** None (requires `ELEVENLABS_API_KEY` configured server-side)

**Request Body:**
```json
{
  "script_id": "a1b2c3d4",
  "language": "en"
}
```

**Language Values:** `en` (English), `hi` (Hindi)

**Response:**
```json
{
  "script_id": "a1b2c3d4",
  "language": "en",
  "audio_url": "/output/audio/a1b2c3d4_en.mp3",
  "duration_seconds": 98.5,
  "status": "completed"
}
```

---

### POST `/api/v1/media/generate_video`

Generate AI avatar video for a script using HeyGen.

**Auth:** None (requires `HEYGEN_API_KEY` configured server-side)

**Request Body:**
```json
{
  "script_id": "a1b2c3d4",
  "language": "en"
}
```

**Response:**
```json
{
  "script_id": "a1b2c3d4",
  "language": "en",
  "video_url": "",
  "status": "pending",
  "heygen_video_id": "hv_abc123xyz"
}
```

**Note:** Video generation is async (30–60s). Status starts as `pending`. Poll or use WebSocket for completion notification.

---

### POST `/api/v1/b2b/portal/generate`

On-demand AI Studio generation. Enterprise tier only. Costs 50 quota credits.

**Auth:** `X-ANN-API-Key` header (enterprise tier required)

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `topic` | string | News topic to generate (e.g., "Bitcoin drops below 50k") |

**Response:**
```json
{
  "status": "processing",
  "message": "Pipeline queued for 'Bitcoin drops below 50k'. Deducted 50 quota.",
  "task_id": "celery-task-uuid"
}
```

**Error Responses:**

| Code | Reason |
|---|---|
| `401` | Invalid API key |
| `402` | Insufficient quota |
| `403` | Tier does not include Studio access |

---

## Pipeline

### POST `/api/v1/pipeline/run`

Run the full autonomous pipeline in the background.

**Auth:** None

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `generate_media` | boolean | `false` | Generate audio + video (costs apply) |
| `source` | string | `newsapi` | Source: `newsapi`, `financial`, `gdelt` |

**Request Body:**
```json
{
  "category": "technology",
  "query": "AI regulation",
  "max_articles": 5
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "Pipeline started. Use /api/v1/pipeline/status/{job_id} to track progress."
}
```

**Execution:** If `REDIS_URL` is set, dispatches to Celery worker. Otherwise uses FastAPI background tasks.

---

### GET `/api/v1/pipeline/status/{job_id}`

Check pipeline job progress.

**Auth:** None

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "writing_script",
  "progress_pct": 45,
  "scripts": [],
  "errors": [],
  "started_at": "2026-06-22T14:30:00Z",
  "completed_at": null
}
```

**Status Values:** `queued` → `ingesting` → `extracting_facts` → `writing_script` → `translating` → `generating_audio` → `generating_video` → `completed` | `failed`

---

### GET `/api/v1/pipeline/jobs`

List recent pipeline jobs.

**Auth:** None

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 20 | Max results (1–100) |

---

## Feeds

### GET `/feed/rss`

Public RSS 2.0 feed. Compatible with any news reader or aggregator.

**Auth:** None

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `category` | string | *all* | Filter by category |
| `limit` | integer | 20 | Max items (1–50) |

**Content-Type:** `application/rss+xml`

---

### GET `/feed/atom`

Public Atom 1.0 feed.

**Auth:** None | **Params:** Same as RSS | **Content-Type:** `application/atom+xml`

---

### GET `/feed/json`

Public JSON Feed 1.1. Developer-friendly format with A.N.N. metadata extensions. Cached for 5 minutes.

**Auth:** None

**Response:**
```json
{
  "version": "https://jsonfeed.org/version/1.1",
  "title": "A.N.N. — AI News Network",
  "home_page_url": "http://localhost:8000/news",
  "feed_url": "http://localhost:8000/feed/json",
  "items": [
    {
      "id": "a1b2c3d4",
      "title": "AI Revolution Reshapes Global Markets",
      "url": "http://localhost:8000/news#script-a1b2c3d4",
      "content_text": "Good evening...",
      "content_hindi": "शुभ संध्या...",
      "summary": "Good evening. In a dramatic turn...",
      "date_published": "2026-06-22T14:30:00Z",
      "tags": ["technology"],
      "_ann": {
        "word_count_en": 245,
        "word_count_hi": 198,
        "duration_seconds": 98
      }
    }
  ]
}
```

---

## Social Media

### POST `/api/v1/social/broadcast/{script_id}`

Manually broadcast a script to all configured social platforms.

**Auth:** None

**Response:**
```json
{
  "twitter": { "status": "posted", "tweet_id": "123456" },
  "facebook": { "status": "posted", "post_id": "789012" },
  "instagram": { "status": "skipped", "reason": "no access token" }
}
```

---

### GET `/api/v1/social/status`

Check which social platforms are configured and active.

**Auth:** None

**Response:**
```json
{
  "enabled_platforms": ["twitter", "facebook"],
  "auto_post": false
}
```

---

### POST `/api/v1/b2b/portal/social-keys`

Link custom social media tokens for Creator Tier auto-posting.

**Auth:** `X-ANN-API-Key` header

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `ig_token` | string | Instagram Graph API token |
| `fb_page_id` | string | Facebook Page ID |
| `linkedin_token` | string | LinkedIn access token |

---

## WebSocket

### WS `/ws/breaking-news`

Real-time WebSocket stream for live news delivery.

**Auth:** `api_key` query parameter (B2B API key required)

**Connection:**
```
ws://localhost:8000/ws/breaking-news?api_key=ann_sk_ent_94f8b22a
```

**Server Push (on new article):**
```json
{
  "id": "a1b2c3d4",
  "headline": "Breaking: AI Summit Announced",
  "english_script": "...",
  "hindi_script": "...",
  "category": "technology",
  "created_at": "2026-06-22T14:30:00Z"
}
```

**Server Push (on studio generation complete):**
```json
{
  "api_key": "ann_sk_ent_94f8b22a",
  "topic": "Bitcoin drops below 50k",
  "video_url": "https://cdn.ann.network/v/abc123.mp4",
  "status": "completed"
}
```

**Connection Errors:**

| Code | Reason |
|---|---|
| `1008` | Missing API key |
| `1008` | Invalid or suspended API key |

---

## System

### GET `/health`

System health check.

**Auth:** None

**Response:**
```json
{
  "status": "A.N.N. Editorial Agent is running.",
  "version": "1.0.0",
  "uptime_seconds": 3621.4,
  "active_jobs": 2
}
```

---

### GET `/api/v1/admin/settings`

Retrieve current system API keys (masked).

**Auth:** None (consider adding admin auth)

**Response:**
```json
{
  "LLM_API_KEY": "sk-p...4xYz",
  "NEWS_API_KEY": "abc1...ef90",
  "ELEVENLABS_API_KEY": "",
  "HEYGEN_API_KEY": "hey_...abc1"
}
```

---

### POST `/api/v1/admin/settings`

Update system API keys at runtime. Writes to `.env` and updates in-memory immediately.

**Auth:** None (consider adding admin auth)

**Request Body:**
```json
{
  "LLM_API_KEY": "sk-new-key-here",
  "NEWS_API_KEY": "new-newsapi-key"
}
```

**Accepted Keys:** `LLM_API_KEY`, `NEWS_API_KEY`, `ALPHA_VANTAGE_KEY`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY`, `TWITTER_BEARER_TOKEN`, `FACEBOOK_PAGE_TOKEN`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID`

---

### GET `/embed/ticker.js`

Embeddable breaking-news ticker widget.

**Usage:**
```html
<script src="http://localhost:8000/embed/ticker.js"></script>
<div id="ann-ticker"></div>
```

---

### GET `/embed/feed.js`

Embeddable news feed card widget.

**Usage:**
```html
<script src="http://localhost:8000/embed/feed.js"></script>
<div id="ann-feed"></div>
```

---

### GET `/api/v1/b2b/portal/metrics`

Get quota and usage metrics for a B2B client.

**Auth:** `X-ANN-API-Key` header

**Response:**
```json
{
  "client_name": "Demo Corp",
  "plan_tier": "enterprise",
  "requests_used": 1250,
  "monthly_quota": 100000
}
```

---

## Data Models

### BroadcastScript

```typescript
{
  id: string                    // 8-char UUID
  headline: string              // AI-generated headline
  english_script: string        // Full EN broadcast script
  hindi_script: string          // Full HI translation
  translations: Record<string, string>  // Additional languages
  category: NewsCategory        // Content category
  source_url: string            // Original source
  word_count_en: number         // English word count
  word_count_hi: number         // Hindi word count
  estimated_duration_seconds: number  // ~150 WPM anchor speed
  created_at: string            // ISO 8601 timestamp
}
```

### NewsCategory

```
general | business | technology | science | health
sports | entertainment | politics | finance | geopolitics
```

### PipelineStatus

```
queued → ingesting → extracting_facts → writing_script
→ translating → generating_audio → generating_video
→ completed | failed
```

### Language

```
en | hi | es | fr | zh | ar
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Code | Meaning |
|---|---|
| `400` | Bad request (validation failed) |
| `401` | Missing or invalid authentication |
| `402` | Insufficient quota / payment required |
| `403` | Forbidden (wrong tier or role) |
| `404` | Resource not found |
| `429` | Rate limit / quota exceeded |
| `500` | Internal server error |

---

## Rate Limits

External API calls are rate-limited server-side:

| Service | Default RPM | Config Key |
|---|---|---|
| LLM (OpenAI/Gemini) | 10 | `LLM_RPM` |
| NewsAPI | 30 | `NEWS_API_RPM` |
| ElevenLabs | 10 | `ELEVENLABS_RPM` |
| HeyGen | 5 | `HEYGEN_RPM` |

B2B clients are limited by their monthly quota (tracked in `requests_used` on each API call).

---

## Quick Start

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Process a single article
curl -X POST http://localhost:8000/api/v1/process_news \
  -H "Content-Type: application/json" \
  -d '{"source_url":"https://example.com","raw_text":"Your article text here, must be at least fifty characters long for processing.","category":"technology"}'

# 3. Run full pipeline
curl -X POST "http://localhost:8000/api/v1/pipeline/run?source=newsapi" \
  -H "Content-Type: application/json" \
  -d '{"category":"technology","max_articles":3}'

# 4. List scripts
curl http://localhost:8000/api/v1/scripts?limit=5

# 5. B2B feed (requires API key)
curl http://localhost:8000/api/v1/b2b/feed/json \
  -H "X-ANN-API-Key: ann_enterprise_a1b2c3d4e5f6"

# 6. WebSocket (requires wscat or similar)
wscat -c "ws://localhost:8000/ws/breaking-news?api_key=ann_enterprise_a1b2c3d4e5f6"
```
