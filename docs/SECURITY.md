# A.N.N. — Security Architecture

> **Version:** 1.0
> **Last Updated:** 2026-06-22
> **Classification:** Internal

---

## Overview

A.N.N. handles sensitive API keys, user credentials, financial transactions, and AI-generated content at scale. This document defines the security architecture across all layers — from user authentication to infrastructure hardening.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY PERIMETER                          │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  WAF /   │   │  TLS    │   │  OAuth2  │   │  RBAC    │    │
│  │  DDoS    │──►│  1.3    │──►│  + JWT   │──►│  Enforce │    │
│  │  Shield  │   │ Termina │   │  Verify  │   │          │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       │                                              │          │
│       ▼                                              ▼          │
│  ┌──────────┐                                 ┌──────────┐    │
│  │  Rate    │                                 │  API Key │    │
│  │  Limiter │                                 │  + Quota │    │
│  └──────────┘                                 └──────────┘    │
│       │                                              │          │
│       └──────────────────┬───────────────────────────┘          │
│                          ▼                                       │
│                   ┌──────────────┐                               │
│                   │  Application │                               │
│                   │    Layer     │                               │
│                   └──────┬───────┘                               │
│                          ▼                                       │
│  ┌──────────┐   ┌──────────────┐   ┌───────────────────┐      │
│  │ Secrets  │   │  Encryption  │   │  Encryption       │      │
│  │ Manager  │   │  At Rest     │   │  In Transit       │      │
│  └──────────┘   └──────────────┘   └───────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. OAuth2

### 1.1 Current Implementation: Supabase Auth

A.N.N. uses **Supabase Auth (GoTrue)** for user-facing authentication in the Orbital Portal.

**Flow:**

```
User (Browser)                     Supabase Auth                    A.N.N. Portal
      │                                 │                                │
      │  1. email + password            │                                │
      │────────────────────────────────►│                                │
      │                                 │  2. Validate credentials       │
      │                                 │     Issue JWT + refresh token  │
      │  3. JWT access token            │                                │
      │◄────────────────────────────────│                                │
      │                                 │                                │
      │  4. Authenticated requests      │                                │
      │────────────────────────────────────────────────────────────────►│
      │     (JWT in Authorization header or Supabase session cookie)     │
```

**Supported Flows:**

| Flow | Endpoint | Status |
|---|---|---|
| Email/Password sign-up | `supabase.auth.signUp()` | ✅ Built |
| Email/Password sign-in | `supabase.auth.signInWithPassword()` | ✅ Built |
| Password reset | `supabase.auth.resetPasswordForEmail()` | ✅ Built |
| Session refresh | Automatic via Supabase client SDK | ✅ Built |
| OAuth2 social login (Google, GitHub) | `supabase.auth.signInWithOAuth()` | 🔲 Planned |
| Magic link (passwordless) | `supabase.auth.signInWithOtp()` | 🔲 Planned |

**Implementation Files:**

| Layer | File | Description |
|---|---|---|
| Frontend auth store | `frontend/web/src/lib/auth-store.ts` | Zustand store wrapping Supabase client |
| Frontend Supabase client | `frontend/web/src/lib/supabase.ts` | Supabase JS client initialization |
| Backend Supabase config | `backend/config.py` | `supabase_url`, `supabase_key` |
| Backend Supabase client | `backend/services/supabase_client.py` | Server-side Supabase SDK |

### 1.2 Target: OAuth2 + PKCE

For the microservice architecture, implement full OAuth2 Authorization Code flow with PKCE:

```
Frontend                    Auth Service                 Supabase
    │                            │                          │
    │  1. /authorize?            │                          │
    │     response_type=code&    │                          │
    │     code_challenge=...     │                          │
    │───────────────────────────►│                          │
    │                            │  2. Validate &           │
    │                            │     proxy to Supabase    │
    │                            │─────────────────────────►│
    │  3. redirect with code     │                          │
    │◄───────────────────────────│◄─────────────────────────│
    │                            │                          │
    │  4. POST /token            │                          │
    │     code + code_verifier   │                          │
    │───────────────────────────►│  5. Exchange code        │
    │                            │─────────────────────────►│
    │  6. JWT access + refresh   │                          │
    │◄───────────────────────────│◄─────────────────────────│
```

---

## 2. JWT

### 2.1 Token Architecture

| Token | Issuer | Lifetime | Storage | Purpose |
|---|---|---|---|---|
| Access token | Supabase GoTrue | 1 hour | Memory (Zustand store) | API authentication |
| Refresh token | Supabase GoTrue | 7 days | HttpOnly cookie (planned) | Silent token refresh |
| B2B API key | A.N.N. backend | Permanent until revoked | `X-ANN-API-Key` header | Commercial API access |
| Admin token | Hardcoded | Permanent | `X-Admin-Token` header | Admin operations |

### 2.2 JWT Verification (Current)

Supabase JWTs are verified client-side by the Supabase SDK. The backend does **not** independently verify JWTs for portal routes — it trusts the Supabase session.

### 2.3 JWT Verification (Target)

```python
# Planned: Backend JWT verification middleware
from jose import jwt, JWTError

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

async def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2.4 Token Security Controls

| Control | Current | Target |
|---|---|---|
| Token storage | localStorage (via Supabase SDK) | HttpOnly secure cookies |
| Token refresh | Automatic (Supabase SDK) | Server-side refresh endpoint |
| Token revocation | Sign-out clears client state | Server-side token blacklist (Redis) |
| CSRF protection | None (SPA architecture) | Double-submit cookie pattern |

---

## 3. RBAC

### 3.1 Current Roles

| Role | Authentication | Access Level |
|---|---|---|
| **Anonymous** | None | Public feeds (`/feed/*`), news page, health check |
| **Portal User** | Supabase Auth (JWT) | Portal dashboard, account settings |
| **B2B Client** | `X-ANN-API-Key` header | Commercial feeds, WebSocket, Studio (enterprise only) |
| **Admin** | `X-Admin-Token` header | Client CRUD, settings management |

### 3.2 B2B Tier Permissions

| Permission | Standard | Pro | Enterprise |
|---|---|---|---|
| JSON/RSS/Atom feeds | ✅ | ✅ | ✅ |
| Monthly API requests | 5,000 | 25,000 | 100,000 |
| WebSocket stream | ❌ | ✅ | ✅ |
| On-Demand Studio | ❌ | ❌ | ✅ (50 credits/gen) |
| Webhook delivery | ✅ | ✅ | ✅ |
| Custom social keys | ❌ | ❌ | ✅ |

**Enforcement (current):**

```python
# Tier check in route handler (backend/main.py:794)
if client.plan_tier != "enterprise":
    raise HTTPException(
        status_code=403,
        detail=f"Your tier ({client.plan_tier}) does not include Studio access."
    )
```

### 3.3 Target RBAC Model

```
┌─────────────────────────────────────────────┐
│                  Roles                       │
│                                               │
│  super_admin ──► Full system access           │
│  editor      ──► Content moderation           │
│  b2b_admin   ──► Client management            │
│  b2b_user    ──► API consumption              │
│  creator     ──► Studio + social              │
│  viewer      ──► Read-only public content     │
└─────────────────────────────────────────────┘
```

Planned implementation via Supabase Row Level Security (RLS) policies + custom `roles` column on the `auth.users` table.

---

## 4. API Rate Limiting

### 4.1 Internal Rate Limiting (External API Calls)

A.N.N. rate-limits outbound calls to external APIs using a **token bucket** algorithm.

**Implementation:** `backend/utils/rate_limiter.py`

```
RateLimiterRegistry (singleton)
    │
    ├── "llm"         → TokenBucket(10 RPM, burst=1)
    ├── "newsapi"     → TokenBucket(30 RPM, burst=1)
    ├── "elevenlabs"  → TokenBucket(10 RPM, burst=1)
    └── "heygen"      → TokenBucket( 5 RPM, burst=1)
```

**Token Bucket Behavior:**

```
Tokens refill continuously at (RPM / 60) tokens/sec
    │
    ▼
Agent calls rate_limiter.acquire("llm")
    │
    ├── Token available → consume, proceed immediately
    └── No tokens → calculate wait time, async sleep, retry
```

| Parameter | Value | Description |
|---|---|---|
| `rate` | RPM / 60 | Tokens added per second |
| `capacity` | 1.0 | Max burst (no request bursting) |
| Blocking | Yes | `acquire()` awaits until token available |
| Scope | Per-service, global | All agents share the same `llm` bucket |

### 4.2 B2B Client Quota Limiting

Each B2B API call increments `requests_used` in the database:

```python
# backend/services/auth.py
if client.requests_used >= client.monthly_quota:
    raise HTTPException(status_code=402, detail="Monthly quota exceeded.")

client.requests_used += 1
await session.commit()
```

| Tier | Monthly Quota | On Exhaust |
|---|---|---|
| Standard | 5,000 | HTTP 402 Payment Required |
| Pro | 25,000 | HTTP 402 Payment Required |
| Enterprise | 100,000 | HTTP 402 Payment Required |
| Studio generation | −50 per request | HTTP 402 if insufficient |

### 4.3 Target: Inbound API Rate Limiting

Planned per-IP and per-key rate limiting on the API Gateway:

| Limit Type | Scope | Limit | Window |
|---|---|---|---|
| Anonymous | Per IP | 60 req | 1 minute |
| Authenticated (B2B) | Per API key | 600 req | 1 minute |
| WebSocket | Per connection | 10 msg | 1 second |
| Admin | Per token | 30 req | 1 minute |
| Pipeline trigger | Global | 10 runs | 1 minute |

Implementation: Redis-backed sliding window counters in the API Gateway service.

---

## 5. WAF (Web Application Firewall)

### 5.1 Current State

No dedicated WAF is deployed. Application-level protections are in place:

| Protection | Implementation | Layer |
|---|---|---|
| Input validation | Pydantic models with `min_length`, type constraints | Application |
| SQL injection | SQLAlchemy ORM (parameterized queries) | Application |
| XSS | React auto-escaping, no `dangerouslySetInnerHTML` | Frontend |
| CORS | FastAPI middleware (currently `allow_origins=["*"]`) | Application |
| Path traversal | FastAPI static file serving (no raw filesystem access) | Framework |
| Request size | Uvicorn default limits | Server |

### 5.2 Target: Cloud WAF

Deploy a managed WAF in front of the API Gateway:

```
Internet ──► CloudFlare / AWS WAF ──► Load Balancer ──► API Gateway
```

**WAF Rules (Planned):**

| Rule | Action | Priority |
|---|---|---|
| OWASP Core Rule Set (CRS) | Block | 1 |
| SQL injection patterns | Block | 2 |
| XSS payloads | Block | 3 |
| Known bad user agents (scanners, bots) | Block | 4 |
| Request body > 10MB | Block | 5 |
| Geographic restrictions (optional) | Allow/Deny list | 6 |
| Rate limit: > 1000 req/min per IP | Rate limit 429 | 7 |
| Bot detection (CAPTCHA challenge) | Challenge | 8 |

### 5.3 Application Security Headers

Target response headers for the Next.js frontend:

```typescript
// next.config.ts (planned)
headers: [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-XSS-Protection", value: "1; mode=block" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://*.supabase.co wss://*.supabase.co https://api.openai.com;"
  },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
]
```

---

## 6. DDoS Protection

### 6.1 Current State

No dedicated DDoS protection. The system relies on:

- Uvicorn's connection limits
- Vercel's built-in edge protection (frontend)
- Supabase's managed infrastructure protection (database)

### 6.2 Target: Multi-Layer DDoS Mitigation

```
Layer 3/4 (Network)          Layer 7 (Application)
┌──────────────────┐         ┌──────────────────┐
│ CloudFlare /     │         │ API Gateway      │
│ AWS Shield       │         │                  │
│                  │         │ • Per-IP limits   │
│ • SYN flood      │         │ • Per-key limits  │
│ • UDP amplify    │         │ • Slowloris       │
│ • BGP blackhole  │         │   detection       │
│                  │         │ • Request queue   │
└──────────────────┘         │   with backpres.  │
                             └──────────────────┘
```

| Layer | Threat | Mitigation | Provider |
|---|---|---|---|
| L3/L4 | Volumetric floods (SYN, UDP, ICMP) | Anycast network, traffic scrubbing | CloudFlare / AWS Shield |
| L7 | HTTP floods, slowloris | Rate limiting, connection timeouts | API Gateway + WAF |
| L7 | WebSocket abuse | Per-connection rate limit, auth required | Application code |
| Application | Pipeline spam | Global pipeline trigger limit, auth for production | Rate limiter |

### 6.3 WebSocket Hardening

Current WebSocket implementation requires a valid B2B API key:

```python
# backend/main.py:896
if not api_key:
    await websocket.close(code=1008, reason="Missing API Authentication.")
    return
```

Additional planned controls:

| Control | Implementation |
|---|---|
| Connection limit per key | Max 5 concurrent WebSocket connections per API key |
| Idle timeout | Disconnect after 5 minutes of no server pushes |
| Message rate limit | Max 10 client messages per second |
| Payload size limit | Max 1KB per client message |

---

## 7. Secrets Manager

### 7.1 Current: `.env` Files

All secrets are stored in `.env` files loaded by `pydantic-settings`:

```
backend/.env                    # Backend secrets (gitignored)
frontend/web/.env.local         # Frontend config (gitignored)
```

**Secret Categories:**

| Category | Variables | Risk Level |
|---|---|---|
| LLM API keys | `LLM_API_KEY` | High — financial exposure |
| News source keys | `NEWS_API_KEY`, `ALPHA_VANTAGE_KEY` | Medium |
| Media API keys | `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY` | High — per-call billing |
| Payment | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Critical — financial |
| Social media | `TWITTER_BEARER_TOKEN`, `FACEBOOK_PAGE_TOKEN`, `INSTAGRAM_ACCESS_TOKEN` | Medium |
| Database | `DATABASE_URL`, `SUPABASE_KEY` | Critical — data access |
| Admin | `ADMIN_SECRET` (default: `superadmin123`) | Critical — full system access |
| Redis | `REDIS_URL` | Medium — cache/queue access |

### 7.2 Runtime Secret Update

Admin can update API keys at runtime via the settings endpoint:

```
POST /api/v1/admin/settings
{ "LLM_API_KEY": "sk-new-key-here" }
```

This writes to the `.env` file via `python-dotenv.set_key()` and updates `os.environ` in-memory. **No restart required.**

**Whitelist:** Only pre-approved keys are accepted:

```python
accepted_keys = [
    "LLM_API_KEY", "NEWS_API_KEY", "ALPHA_VANTAGE_KEY",
    "ELEVENLABS_API_KEY", "HEYGEN_API_KEY",
    "TWITTER_BEARER_TOKEN", "FACEBOOK_PAGE_TOKEN",
    "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"
]
```

### 7.3 Known Vulnerabilities

| Issue | Severity | Current State | Remediation |
|---|---|---|---|
| Admin token is hardcoded default | **Critical** | `superadmin123` | Move to env var, enforce strong value |
| Settings endpoint has no auth | **High** | Anyone can read/write API keys | Add admin token requirement |
| API keys stored in plaintext | **High** | `.env` file on disk | Migrate to secrets manager |
| Supabase anon key in frontend | Low | Expected — anon key is public-safe | RLS policies protect data |
| B2B API keys stored in plaintext DB | **Medium** | `ClientAPIKey.api_key` column | Hash with bcrypt, compare on auth |

### 7.4 Target: Cloud Secrets Manager

```
┌─────────────────────────────────────────────┐
│           Secrets Manager                    │
│        (AWS SSM / GCP Secret Manager         │
│         / HashiCorp Vault)                   │
│                                               │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ API Keys    │  │ Database Credentials │  │
│  │             │  │                      │  │
│  │ LLM_API_KEY │  │ DATABASE_URL         │  │
│  │ STRIPE_*    │  │ SUPABASE_KEY         │  │
│  │ HEYGEN_*    │  │ REDIS_URL            │  │
│  └─────────────┘  └──────────────────────┘  │
│                                               │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Social      │  │ Infrastructure       │  │
│  │             │  │                      │  │
│  │ TWITTER_*   │  │ ADMIN_SECRET         │  │
│  │ FACEBOOK_*  │  │ JWT_SECRET           │  │
│  │ INSTAGRAM_* │  │ WEBHOOK_SECRET       │  │
│  └─────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────┘
          │
          │  Injected at deploy time
          ▼
    ┌──────────────┐
    │  Kubernetes   │
    │  Secrets or   │
    │  Env Vars     │
    └──────────────┘
```

**Migration plan:**

1. Move all secrets from `.env` to cloud secrets manager
2. Inject as Kubernetes Secrets or environment variables at deploy
3. Rotate all credentials after migration
4. Remove `.env` file from production servers
5. Implement automatic secret rotation for high-risk keys

---

## 8. Encryption At Rest

### 8.1 Database

| Data Store | Encryption | Implementation |
|---|---|---|
| Supabase Postgres (cloud) | ✅ AES-256 | Managed by Supabase — transparent disk encryption |
| SQLite (local dev) | ❌ None | Development only — no sensitive data in production |
| Redis cache | ❌ None | Ephemeral data only (cache, rate limits, job queue) |
| Generated media files | ❌ None | Stored in `backend/output/` on local disk |

### 8.2 Sensitive Fields

| Field | Current Storage | Target |
|---|---|---|
| B2B API keys | Plaintext in DB (`client_api_keys.api_key`) | bcrypt hash (compare on auth) |
| User passwords | Supabase-managed (bcrypt) | No change — already secure |
| Social media tokens | Plaintext in `.env` | Encrypted in secrets manager |
| Stripe webhook secret | Plaintext in `.env` | Encrypted in secrets manager |
| Client social tokens | Not persisted (comment in code) | Fernet encryption at rest |

### 8.3 Target: Field-Level Encryption

For sensitive client data (social tokens, custom API keys):

```python
# Planned: Fernet symmetric encryption for client secrets
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_field(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_field(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
```

### 8.4 Media Asset Security

| Asset Type | Storage | Access Control |
|---|---|---|
| Generated audio (.mp3) | `backend/output/audio/` | No auth (served via static files) |
| Generated video (.mp4) | HeyGen CDN → `backend/output/video/` | No auth |
| Thumbnails | Not yet implemented | — |

**Target:** Signed URLs with expiration for all media assets (S3 presigned URLs or Supabase Storage policies).

---

## 9. Encryption In Transit

### 9.1 Current State

| Connection | Protocol | Encrypted | Certificate |
|---|---|---|---|
| Browser → Frontend (Vercel) | HTTPS / TLS 1.3 | ✅ | Vercel-managed Let's Encrypt |
| Browser → Backend (local dev) | HTTP | ❌ | None — `localhost:8000` |
| Frontend → Supabase | HTTPS / TLS 1.3 | ✅ | Supabase-managed |
| Backend → OpenAI API | HTTPS / TLS 1.3 | ✅ | OpenAI certificate |
| Backend → ElevenLabs API | HTTPS / TLS 1.3 | ✅ | ElevenLabs certificate |
| Backend → HeyGen API | HTTPS / TLS 1.3 | ✅ | HeyGen certificate |
| Backend → NewsAPI | HTTPS / TLS 1.3 | ✅ | NewsAPI certificate |
| Backend → Supabase Postgres | TLS | ✅ | Supabase-managed |
| Backend → Redis (local) | TCP | ❌ | None — `localhost:6379` |
| Backend → Celery Worker | Redis broker | ❌ | Same Redis connection |
| WebSocket (local) | WS | ❌ | None — `ws://localhost:8000` |
| WebSocket (production) | WSS | ✅ | Via reverse proxy / load balancer |
| Webhook delivery | HTTPS | ✅ | Client's certificate |

### 9.2 Target: Full TLS Coverage

```
                          ┌──────────────────┐
Internet ──── TLS 1.3 ───►│  Load Balancer   │
                          │  (TLS termination)│
                          └────────┬─────────┘
                                   │
                          mTLS (internal)
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ API GW   │ │ Auth Svc │ │ Article  │
              └──────────┘ └──────────┘ └──────────┘
                    │              │              │
                    └──── TLS ─────┼──── TLS ─────┘
                                   ▼
                          ┌──────────────┐
                          │ Redis (TLS)  │
                          │ Postgres(TLS)│
                          └──────────────┘
```

| Connection | Target Protocol | Implementation |
|---|---|---|
| Client → API Gateway | TLS 1.3 | Certificate via Let's Encrypt / ACM |
| Inter-service (API GW → services) | mTLS | Istio service mesh or manual cert rotation |
| Service → Redis | TLS | `rediss://` URL scheme, `ssl=True` |
| Service → Postgres | TLS | `sslmode=require` in connection string |
| WebSocket | WSS | TLS termination at load balancer |
| Webhook delivery | HTTPS | Verify client certificate chain |

### 9.3 Certificate Management

| Environment | Method |
|---|---|
| Local development | Self-signed certs (optional) or plain HTTP |
| Staging | Let's Encrypt (auto-renewal via cert-manager) |
| Production | AWS ACM / Cloudflare managed certificates |
| Inter-service mTLS | cert-manager + Istio (Kubernetes) |

---

## Security Roadmap

### Immediate (P0 — Critical)

- [ ] Change default admin token from `superadmin123` to a strong env-var-injected secret
- [ ] Add authentication to `GET/POST /api/v1/admin/settings` endpoints
- [ ] Restrict CORS `allow_origins` from `["*"]` to specific domains
- [ ] Hash B2B API keys with bcrypt before storing in database

### Short-Term (P1 — High)

- [ ] Backend JWT verification for all authenticated routes (not just client-side)
- [ ] HttpOnly secure cookies for Supabase session tokens
- [ ] Security response headers (CSP, HSTS, X-Frame-Options) on Next.js
- [ ] Per-IP inbound rate limiting on API Gateway
- [ ] Signed URLs for media asset access
- [ ] Webhook payload signing (HMAC-SHA256)

### Medium-Term (P2 — Medium)

- [ ] Cloud secrets manager (AWS SSM / GCP Secret Manager / HashiCorp Vault)
- [ ] TLS for Redis connections
- [ ] WAF deployment (CloudFlare or AWS WAF with OWASP CRS)
- [ ] DDoS protection (CloudFlare / AWS Shield)
- [ ] Audit logging for all admin and auth operations
- [ ] Fernet field-level encryption for client social tokens
- [ ] API key rotation with grace period

### Long-Term (P3 — Hardening)

- [ ] mTLS for inter-service communication
- [ ] SOC 2 Type II compliance audit
- [ ] Penetration testing (annual)
- [ ] RBAC with Supabase RLS policies
- [ ] OAuth2 social login (Google, GitHub)
- [ ] Automatic secret rotation
- [ ] SIEM integration (security event monitoring)
- [ ] Bug bounty program
