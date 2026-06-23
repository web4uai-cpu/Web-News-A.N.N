# A.N.N. — Implementation Plan

> **Version:** 1.0
> **Created:** 2026-06-23
> **Timeline:** 18 months (36 sprints × 2 weeks)
> **Team:** Solo developer → scaling to 3–5 engineers by Phase 5

---

## Executive Summary

This document is the sprint-level execution plan for building A.N.N. from its current monolith state into a production-grade, revenue-generating, enterprise-scale autonomous news network. It covers 4 remaining phases (Phases 1–2 are complete), broken into 2-week sprints with specific deliverables.

**Current State (Completed):**
- Phase 1: FastAPI monolith with 5 AI agents, media production, social posting, Stripe billing
- Phase 2: Next.js 16 frontend (homepage, news, dashboard, portal), 7 docs, microservice scaffold

**What's Next:**
- Phase 3: Decompose monolith → 7 microservices (Month 1–4)
- Phase 4: Upgrade AI agents → autonomous, memory-equipped, RAG-grounded (Month 3–6)
- Phase 5: Scale to new channels, languages, and mobile (Month 5–10)
- Phase 6: Enterprise products, compliance, and revenue maximization (Month 8–18)

---

## Phase 3: Microservice Migration

> **Goal:** Decompose the FastAPI monolith into independently deployable, scalable services.
> **Duration:** 8 sprints (16 weeks / 4 months)
> **Prerequisites:** Redis running, Docker installed, Supabase project active

### Sprint 1–2: API Gateway + Auth Service (Weeks 1–4)

**Sprint 1: API Gateway**

| Task | Description | File(s) |
|---|---|---|
| Bootstrap FastAPI app | Create `main.py` with health check, CORS, Prometheus | `backend/api-gateway/main.py` |
| Route registry | Define route table mapping paths → downstream services | `backend/api-gateway/routes.py` |
| HTTP proxy | Forward requests to downstream services via `httpx` | `backend/api-gateway/proxy.py` |
| Rate limiter (inbound) | Redis-backed sliding window per-IP and per-API-key | `backend/api-gateway/rate_limiter.py` |
| Auth middleware | Extract and validate JWT/API-key, inject user context | `backend/api-gateway/middleware.py` |
| Docker + Compose | Dockerfile + add to `docker-compose.yml` on port 8000 | `backend/api-gateway/Dockerfile` |

**Sprint 2: Auth Service**

| Task | Description | File(s) |
|---|---|---|
| Bootstrap FastAPI app | Standalone auth service on port 8001 | `backend/auth-service/main.py` |
| Supabase auth wrapper | Sign-up, sign-in, password reset, session refresh | `backend/auth-service/supabase_auth.py` |
| JWT verification | Verify Supabase JWTs server-side with `python-jose` | `backend/auth-service/jwt.py` |
| API key CRUD | Migrate `ClientAPIKey` model, create/list/revoke endpoints | `backend/auth-service/api_keys.py` |
| Quota enforcement | Check and increment `requests_used` per API call | `backend/auth-service/quota.py` |
| DB migration | Alembic migration for `client_api_keys` table in Postgres | `backend/auth-service/alembic/` |
| Admin routes | Migrate `/api/v1/admin/clients`, `/api/v1/admin/settings` | `backend/auth-service/admin.py` |

**Definition of Done:**
- [ ] Gateway proxies all existing endpoints without breaking the frontend
- [ ] Auth service handles login/signup/API-key validation independently
- [ ] All existing API tests pass through the gateway
- [ ] Docker Compose runs gateway + auth + old monolith together

**Risks:**
- Session state split between Supabase client-side and server-side verification
- Mitigation: Share JWT secret via env var, validate on both sides

---

### Sprint 3–4: Article Service + Video Service (Weeks 5–8)

**Sprint 3: Article Service**

| Task | Description | Source (monolith) |
|---|---|---|
| Script CRUD API | `GET/POST /scripts`, `GET /scripts/{id}`, `GET /scripts/latest` | `main.py:426–462` |
| Persistent storage | Migrate from in-memory `script_store` dict → Postgres table | `main.py:66` |
| Feed generation | RSS, Atom, JSON feed endpoints | `main.py:514–597`, `feeds/` |
| B2B feed | Premium feed with API key auth (calls auth-service) | `main.py:584–596` |
| Category filtering | Filter scripts by category across all feed types | `main.py:521–525` |
| Embed widgets | Ticker and feed JS widget endpoints | `main.py:917–928` |
| Supabase sync | Keep `broadcast_scripts` table in sync | `services/supabase_client.py` |

**Sprint 4: Video Service**

| Task | Description | Source (monolith) |
|---|---|---|
| Audio generation API | `POST /media/generate_audio` | `main.py:467–485`, `media/elevenlabs_tts.py` |
| Video generation API | `POST /media/generate_video` | `main.py:488–506`, `media/heygen_video.py` |
| Celery integration | Async generation via Celery workers | `services/tasks.py` |
| Media storage | File management for `output/audio/` and `output/video/` | `media/` |
| Status tracking | Job status for long-running HeyGen renders | `media/heygen_video.py` |
| Signed URLs (new) | Generate expiring URLs for media access | New |

**Definition of Done:**
- [ ] Scripts persist across restarts (Postgres-backed)
- [ ] RSS/Atom/JSON feeds serve from article-service
- [ ] Audio/video generation works independently from article creation
- [ ] Frontend works unchanged (API contract preserved)

---

### Sprint 5–6: Notification + Analytics + Search (Weeks 9–12)

**Sprint 5: Notification Service**

| Task | Description | Source (monolith) |
|---|---|---|
| Social posting | Twitter, Facebook, Instagram auto-posting | `social/*.py` |
| Webhook delivery | Push to B2B client webhook URLs with retry | `services/webhook.py` |
| WebSocket manager | Breaking news real-time stream | `main.py:823–912` |
| Redis Pub/Sub | Listen for Celery completions, broadcast to WS clients | `main.py:858–880` |
| Scheduling | Optimal posting time selection per platform | `social/social_scheduler.py` |

**Sprint 6: Analytics + Search Services**

| Task | Description |
|---|---|
| Analytics: Event ingestion | Track page views, API calls, video plays |
| Analytics: Prometheus export | Custom metrics (articles/hr, avg latency, agent scores) |
| Analytics: Dashboard API | Endpoints for Control Center panels |
| Search: Full-text index | Postgres `tsvector` or Meilisearch for script search |
| Search: API | `GET /search?q=...&category=...&limit=...` |

**Definition of Done:**
- [ ] Social posts fire from notification-service, not monolith
- [ ] WebSocket stream works through the API gateway
- [ ] Search returns relevant results within 100ms
- [ ] Analytics tracks all API calls with per-client attribution

---

### Sprint 7–8: Integration + Kubernetes (Weeks 13–16)

**Sprint 7: Inter-Service Communication**

| Task | Description |
|---|---|
| Service discovery | Environment-based service URLs (Docker DNS in compose) |
| Redis Streams | Event bus for async events (article.created, video.ready) |
| Pipeline orchestrator | Rewrite `NewsPipeline` to call services via HTTP/events |
| Error handling | Circuit breaker pattern for downstream service failures |
| Health checks | `/health` endpoint on every service, compose healthchecks |
| Shared libs | Extract common code (logger, config, models) into shared package |

**Sprint 8: Kubernetes + CI/CD**

| Task | Description |
|---|---|
| K8s manifests | Deployment + Service + HPA for each microservice | 
| Ingress | NGINX ingress controller with TLS termination |
| ConfigMaps/Secrets | Externalize all env vars into K8s resources |
| Helm chart (optional) | Parameterized deployment for staging/prod |
| CI pipeline | GitHub Actions: lint → test → build → push → deploy |
| Staging environment | Deploy to a staging K8s namespace |

**Definition of Done:**
- [ ] All 7 services run independently in Docker Compose
- [ ] `docker-compose up` starts the full stack with service discovery
- [ ] K8s manifests deploy to a staging cluster
- [ ] CI pipeline runs on every push to `main`
- [ ] Zero downtime deployment via rolling updates

**Tech Decisions:**
| Decision | Choice | Rationale |
|---|---|---|
| Inter-service sync | HTTP (httpx) | Simple, debuggable, good enough for current scale |
| Inter-service async | Redis Streams | Already have Redis, no Kafka overhead |
| Service discovery | Docker DNS / K8s DNS | No extra infra needed |
| CI/CD | GitHub Actions | Free for public repos, native Docker support |

---

## Phase 4: Advanced AI Agents

> **Goal:** Upgrade agents from stateless LLM wrappers to autonomous, memory-equipped, RAG-grounded units.
> **Duration:** 6 sprints (12 weeks / 3 months)
> **Prerequisites:** Phase 3 Sprint 1–4 complete (services can run independently)
> **Overlap:** Can start during Phase 3 Sprint 5 (agents are independent of microservice migration)

### Sprint 9–10: Agent Orchestrator + RAG (Weeks 17–20)

**Sprint 9: LangGraph Orchestrator**

| Task | Description |
|---|---|
| Install LangGraph | Add to `agents/orchestrator/requirements.txt` |
| Define DAG | 10-agent pipeline as a LangGraph StateGraph |
| State schema | Pydantic model for pipeline state passed between nodes |
| Conditional edges | Critic review → rewrite loop as conditional edge |
| Parallel execution | Headline + Translation as parallel branches |
| Retry nodes | Per-node retry with exponential backoff |
| Observability | LangSmith tracing integration (optional) |

**Sprint 10: RAG Pipeline**

| Task | Description |
|---|---|
| Embedding service | Generate embeddings for all articles via OpenAI `text-embedding-3-small` |
| Vector store | pgvector extension on Supabase Postgres |
| Ingestion pipeline | On article creation → chunk → embed → store |
| Retrieval | Semantic search for fact-checking context |
| Integration | Fact Agent queries RAG before verification |
| Knowledge base | Seed with trusted source corpus (Wikipedia, official feeds) |

**Definition of Done:**
- [ ] Pipeline runs via LangGraph DAG instead of sequential function calls
- [ ] Fact Agent retrieves relevant prior articles for cross-referencing
- [ ] RAG improves fact-checking accuracy (measure: hallucination rate drops)

---

### Sprint 11–12: New Agents (Weeks 21–24)

**Sprint 11: Discovery + Legal Agents**

| Task | Description |
|---|---|
| Discovery Agent | Multi-source ingestion with semantic deduplication |
| Dedup algorithm | Cosine similarity on embeddings, threshold 0.85 |
| Relevance scoring | LLM-scored relevance (1–10) with category matching |
| Breaking detection | Anomaly detection on topic frequency spike |
| Legal Agent | Copyright scan (match against source text, flag >30% overlap) |
| Defamation check | LLM scan for potentially defamatory statements |
| GDPR compliance | PII detection and redaction |

**Sprint 12: SEO Agent + Publishing Agent**

| Task | Description |
|---|---|
| SEO Agent | Keyword extraction from script content |
| Meta generation | Auto-generate meta title, description, OG tags |
| Schema.org | NewsArticle structured data for each script |
| Internal linking | Suggest related articles based on embedding similarity |
| Publishing Agent | Orchestrate multi-channel distribution |
| Platform adapters | Format content per platform (Twitter 280 chars, IG square, etc.) |
| Scheduling | Optimal post time based on historical engagement data |

**Definition of Done:**
- [ ] Duplicate articles rejected before entering pipeline
- [ ] Legal scan catches copyright violations (test with known copyrighted text)
- [ ] SEO metadata auto-generated for every published article
- [ ] Publishing agent distributes to all configured channels

---

### Sprint 13–14: Agent Memory + Prompt Engineering (Weeks 25–28)

**Sprint 13: Memory System**

| Task | Description |
|---|---|
| Short-term memory | Redis-backed buffer: last 100 article hashes, batch context |
| Long-term memory | Postgres tables: source reputation, topic frequency, quality baselines |
| Translation glossary | Consistent proper noun translations across sessions |
| Memory API | Read/write interface for all agents to access shared memory |
| Decay strategy | Age-weighted memory with automatic pruning |

**Sprint 14: Prompt Library + A/B Testing**

| Task | Description |
|---|---|
| Prompt versioning | `ai/prompts/` directory with YAML prompt definitions |
| Prompt registry | Load prompts by name + version at runtime |
| A/B testing framework | Random assignment of prompt variants per pipeline run |
| Performance scoring | Critic score + engagement metrics per prompt variant |
| Auto-promotion | Winning variant auto-promoted after statistical significance |
| Dashboard integration | Prompt performance visible in Control Center |

**Definition of Done:**
- [ ] Agents remember prior articles and avoid redundant coverage
- [ ] Translation glossary ensures "Apple" is always transliterated consistently
- [ ] Prompt A/B test shows measurable quality difference between variants
- [ ] Control Center displays agent performance metrics

**Tech Decisions:**
| Decision | Choice | Rationale |
|---|---|---|
| Orchestration | LangGraph | Native Python, state management, conditional edges |
| Vector DB | pgvector (Supabase) | No new infrastructure, SQL-queryable |
| Embeddings | `text-embedding-3-small` | Cost-effective, 1536 dims, good quality |
| Memory store | Redis (short) + Postgres (long) | Already in stack |
| Prompt format | YAML with Jinja2 templates | Human-readable, version-controllable |

---

## Phase 5: Scale & Distribution

> **Goal:** Expand A.N.N. to new channels, languages, and platforms.
> **Duration:** 10 sprints (20 weeks / 5 months)
> **Prerequisites:** Phase 3 complete, Phase 4 Sprint 9–12 complete
> **Team:** Scale to 2–3 engineers (1 backend, 1 mobile, 1 infra)

### Sprint 15–16: YouTube + Telegram (Weeks 29–32)

**Sprint 15: YouTube Upload Pipeline**

| Task | Description |
|---|---|
| Google OAuth2 | YouTube Data API v3 authentication flow |
| Upload service | Automated video upload with title, description, tags |
| Thumbnail gen | Auto-generate thumbnails from article content (Pillow/Sharp) |
| SEO metadata | Map SEO Agent output to YouTube tags and description |
| Scheduling | Upload at optimal times based on channel analytics |
| Playlist mgmt | Auto-categorize into playlists by news category |

**Sprint 16: Telegram + WhatsApp**

| Task | Description |
|---|---|
| Telegram Bot | Bot API integration for channel message posting |
| Message formatting | Markdown-formatted news summaries with links |
| Media attachments | Attach audio/video to Telegram messages |
| WhatsApp Business | WhatsApp Cloud API for channel broadcasts |
| Template messages | Pre-approved message templates for WhatsApp |
| Subscriber mgmt | Track channel subscribers for analytics |

**Definition of Done:**
- [ ] Videos auto-upload to YouTube within 5 minutes of generation
- [ ] Telegram channel receives formatted news with media
- [ ] WhatsApp channel sends approved template messages

---

### Sprint 17–18: Mobile App (Weeks 33–36)

**Sprint 17: React Native Setup + Core Screens**

| Task | Description |
|---|---|
| Expo project | Initialize in `frontend/mobile/` with TypeScript |
| Navigation | React Navigation with tab bar (Home, Categories, Video, Settings) |
| News feed | Scrollable feed with category filters (reuse `api.ts` types) |
| Article reader | Full article view with EN/HI toggle |
| Auth | Supabase Auth integration (same as web) |
| Theming | Dark theme matching web frontend |

**Sprint 18: Media + Push Notifications**

| Task | Description |
|---|---|
| Video player | In-app video playback for AI broadcasts |
| Audio player | Background audio playback for TTS scripts |
| Push notifications | Expo push + backend notification service integration |
| Breaking alerts | Push on breaking news (WebSocket → push service) |
| Offline mode | Cache recent articles for offline reading |
| App store prep | Icons, splash screen, store listing |

**Definition of Done:**
- [ ] iOS and Android builds via Expo EAS
- [ ] News feed loads and scrolls smoothly (60fps)
- [ ] Push notifications fire on breaking news
- [ ] Offline reading works for cached articles

---

### Sprint 19–20: Multi-Language + Short-Form Video (Weeks 37–40)

**Sprint 19: Language Expansion**

| Task | Description |
|---|---|
| Arabic support | RTL layout support in web + mobile |
| Spanish support | Translation agent + voice clone |
| French support | Translation agent + voice clone |
| Language selector | User preference stored in profile |
| Voice clone training | ElevenLabs voice clones per new language |
| Avatar variants | HeyGen avatars per language/region |

**Sprint 20: Short-Form Video**

| Task | Description |
|---|---|
| Vertical format | 9:16 video generation for Reels/Shorts/TikTok |
| Script adapter | Truncate scripts to 30s for short-form |
| Caption overlay | Burned-in captions with word-level timing |
| Platform upload | Auto-post to Instagram Reels, YouTube Shorts, TikTok |
| A/B testing | Test vertical vs horizontal engagement |

---

### Sprint 21–24: Infrastructure Hardening (Weeks 41–48)

**Sprint 21–22: Terraform + CDN**

| Task | Description |
|---|---|
| Terraform modules | VPC, EKS cluster, RDS, ElastiCache, S3 |
| Environment parity | Staging and production share same Terraform modules |
| CDN setup | CloudFront for media assets (audio, video, thumbnails) |
| Signed URLs | S3 presigned URLs with 1-hour expiry |
| SSL/TLS | ACM certificates for all domains |
| DNS | Route 53 with health checks and failover |

**Sprint 23–24: Multi-Region + Monitoring**

| Task | Description |
|---|---|
| Multi-region | Deploy to US-East + EU-West + AP-South |
| Database replication | Supabase read replicas per region |
| Redis cluster | ElastiCache cluster mode with cross-region replication |
| Alerting | PagerDuty/Slack alerts on error rate > 1%, latency > 500ms |
| Logging | Centralized logging via Loki or CloudWatch |
| Status page | Public status page (Statuspage.io or custom) |

**Definition of Done:**
- [ ] `terraform apply` provisions full infrastructure
- [ ] Media served via CDN with <100ms latency globally
- [ ] Multi-region deployment handles regional failover
- [ ] Alerts fire within 60 seconds of incident

**Tech Decisions:**
| Decision | Choice | Rationale |
|---|---|---|
| Mobile framework | React Native (Expo) | Shared TypeScript, single codebase iOS+Android |
| Push notifications | Expo Push + FCM/APNS | Free tier generous, Expo handles complexity |
| IaC | Terraform | Multi-cloud capable, state management, modules |
| CDN | CloudFront | Tight S3 integration, global edge network |
| Short-form video | ffmpeg + custom | No vendor lock-in, subtitle burn-in control |

---

## Phase 6: Enterprise & Revenue

> **Goal:** Maximize revenue, achieve compliance, and build enterprise-grade products.
> **Duration:** 12 sprints (24 weeks / 6 months)
> **Prerequisites:** Phase 3–4 complete, Phase 5 Sprint 15–18 complete
> **Team:** 3–5 engineers + 1 sales/BD

### Sprint 25–26: Admin Dashboard + Content Moderation (Weeks 49–52)

**Sprint 25: Admin Dashboard**

| Task | Description |
|---|---|
| Next.js app | `frontend/admin/` — internal admin panel |
| RBAC | super_admin, editor, viewer roles via Supabase RLS |
| User management | List, suspend, upgrade B2B clients |
| System health | Real-time service health from all microservices |
| Pipeline monitor | Live pipeline runs with per-agent timing |
| Revenue dashboard | Stripe revenue, MRR, churn rate (Recharts) |

**Sprint 26: Content Moderation**

| Task | Description |
|---|---|
| Moderation queue | Articles flagged by Legal Agent appear in review queue |
| Human-in-the-loop | Editor can approve, reject, or edit flagged content |
| Audit log | Immutable log of all moderation decisions |
| Auto-rules | Configurable auto-block rules (keywords, sources) |
| Feedback loop | Editor corrections improve Legal Agent prompts |

---

### Sprint 27–28: Advertising + Premium Subscriptions (Weeks 53–56)

**Sprint 27: Ad Integration**

| Task | Description |
|---|---|
| AdSense setup | Google AdSense account, `ads.txt`, ad components |
| Ad placements | Leaderboard, in-feed, sidebar, mobile anchor |
| Native ads | Sponsored article card component with "Sponsored" label |
| Ad-free flag | Premium users see no ads |
| Affiliate engine | Keyword → affiliate URL injection service |
| Revenue tracking | Ad impression/click tracking in analytics service |

**Sprint 28: Premium Membership**

| Task | Description |
|---|---|
| Stripe subscriptions | Convert from one-time payment to `mode="subscription"` |
| Tier gating | Paywall component (3 free articles → gate) |
| Audio access | TTS playback UI for Creator+ tiers |
| Email digest | Daily/weekly AI briefing email pipeline |
| Referral program | Invite link → 1 month free for referrer |
| Billing portal | Stripe Customer Portal for plan management |

---

### Sprint 29–30: Enterprise API Expansion (Weeks 57–60)

**Sprint 29: Enterprise Tiers**

| Task | Description |
|---|---|
| Scale tier | 500K requests/mo, $1,999 — dedicated Celery workers |
| Unlimited tier | Unlimited requests, $4,999 — SLA 99.99% |
| Custom onboarding | Enterprise sign-up flow with contract review |
| Usage analytics | Per-client API usage dashboard |
| Webhook filtering | Subscribe to specific categories/keywords only |
| Historical backfill | 90+ day archive access for enterprise clients |

**Sprint 30: White-Label Platform**

| Task | Description |
|---|---|
| Theming engine | Dynamic branding (logo, colors, fonts) via config |
| Multi-tenant DB | Row-level isolation per white-label client |
| Custom domains | Client subdomains with SSL via Let's Encrypt |
| Voice onboarding | ElevenLabs voice clone setup per client |
| Avatar onboarding | HeyGen avatar selection/training per client |
| SLA monitoring | Per-client uptime and performance tracking |

---

### Sprint 31–32: AI Research Products (Weeks 61–64)

**Sprint 31: Research Report Pipeline**

| Task | Description |
|---|---|
| Research Writer Agent | Long-form 5,000+ word analysis agent |
| Deep ingestion | 50+ article ingestion per report topic |
| Chart generation | Recharts server-side rendering for data viz |
| PDF generation | HTML → PDF conversion (Puppeteer or WeasyPrint) |
| Delivery | Email + dashboard download |
| Subscription | Daily/Weekly/Monthly report subscriptions |

**Sprint 32: Market Intelligence Dashboard**

| Task | Description |
|---|---|
| Sentiment Agent | Real-time sentiment scoring per stock/sector |
| Event timeline | Chronological market-moving events view |
| Impact scoring | AI-predicted market impact (1–10) per event |
| Alert engine | Push on sentiment shift threshold |
| Export API | REST + WebSocket for intelligence data |
| Institutional pricing | $2,000/mo tier with dedicated support |

---

### Sprint 33–34: Government Intelligence (Weeks 65–68)

**Sprint 33: OSINT Pipeline**

| Task | Description |
|---|---|
| Government sources | Jane's, UN, NATO, OSCE press release ingestion |
| Threat Classification Agent | Categorize events by threat type/severity |
| Entity Resolution Agent | Link analysis across articles (people, orgs, locations) |
| Geolocation Agent | Map events to geographic coordinates |
| Confidence scoring | Multi-source verification with confidence levels |

**Sprint 34: Compliance + Packaging**

| Task | Description |
|---|---|
| SOC 2 audit prep | Evidence collection, policy documentation |
| Audit logging | Immutable, tamper-proof log of all data access |
| Data residency | Region-specific deployment option (US, EU, IN) |
| OSINT products | Package into Daily Brief, Threat Monitor, Risk Score |
| Pricing | $5K–$50K/mo tiers for government/defense |

---

### Sprint 35–36: Hardening + Launch (Weeks 69–72)

**Sprint 35: Security Hardening**

| Task | Description |
|---|---|
| WAF deployment | CloudFlare WAF with OWASP Core Rule Set |
| DDoS protection | CloudFlare / AWS Shield Advanced |
| mTLS | Inter-service mutual TLS via Istio |
| Secret rotation | Automated key rotation with grace periods |
| Penetration test | External pentest engagement |
| Bug bounty | Launch bug bounty program (HackerOne) |

**Sprint 36: Production Launch**

| Task | Description |
|---|---|
| Load testing | k6 load test: 1000 concurrent users, 100 req/s |
| Chaos testing | Kill random service pods, verify recovery |
| Documentation | Final pass on all docs, API changelog |
| Marketing site | Landing page for enterprise sales |
| Sales enablement | Demo environment, pitch deck, pricing page |
| Launch | Public launch, Product Hunt, Hacker News |

---

## Dependency Graph

```
Phase 3 (Microservices)                    Phase 4 (AI Agents)
├─ Sprint 1-2: Gateway + Auth             ├─ Sprint 9-10: Orchestrator + RAG
├─ Sprint 3-4: Article + Video ◄──────────┤  (can start after Sprint 4)
├─ Sprint 5-6: Notification + Analytics   ├─ Sprint 11-12: New Agents
├─ Sprint 7-8: Integration + K8s         ├─ Sprint 13-14: Memory + Prompts
│                                          │
▼                                          ▼
Phase 5 (Scale)                           Phase 6 (Enterprise)
├─ Sprint 15-16: YouTube + Telegram       ├─ Sprint 25-26: Admin + Moderation
├─ Sprint 17-18: Mobile App               ├─ Sprint 27-28: Ads + Premium
├─ Sprint 19-20: Languages + Shorts       ├─ Sprint 29-30: Enterprise API + White Label
├─ Sprint 21-24: Infra Hardening          ├─ Sprint 31-32: Research + Intelligence
                                          ├─ Sprint 33-34: Government + Compliance
                                          └─ Sprint 35-36: Hardening + Launch
```

**Critical Path:** Sprint 1 → 3 → 5 → 7 → 15 → 25 → 35 → 37

**Parallel Tracks:**
- Phase 4 (AI agents) can run in parallel with Phase 3 Sprint 5+ (agents are independent of service split)
- Phase 5 Sprint 17–18 (mobile) can run in parallel with Sprint 19–20 (languages) with a second developer
- Phase 6 Sprint 31–34 (research + government) can run in parallel with Sprint 27–30
- Phase 7 can start after Phase 4 is complete (builds on agent infrastructure)

---

## Phase 7: AI v2 — Next-Gen Intelligence

> **Goal:** Upgrade agents to multi-modal, self-improving, real-time fact-checked autonomous units.
> **Duration:** 6 sprints (12 weeks / 3 months)
> **Prerequisites:** Phase 4 complete (LangGraph pipeline, RAG, memory system)

### Sprint 37–38: Multi-Modal Agents (Weeks 73–76)

**Sprint 37: Image Generation Agent**

| Task | Description | File(s) |
|---|---|---|
| Thumbnail generator | AI-generated editorial thumbnails per article | `agents/vision-agent/image_generator.py` |
| Social media cards | Platform-specific image variants (Twitter, IG, YouTube) | `agents/vision-agent/image_generator.py` |
| Infographic generator | Data visualization images from article statistics | `agents/vision-agent/image_generator.py` |
| Prompt templates | YAML-based image generation prompts with A/B variants | `ai/prompts/templates/image_generator.yaml` |
| Pipeline integration | Add thumbnail/social images to PipelineState | `agents/orchestrator/state.py` |

**Sprint 38: Video Understanding Agent**

| Task | Description | File(s) |
|---|---|---|
| Keyframe extraction | FFmpeg-based keyframe extraction at configurable intervals | `agents/vision-agent/video_understanding.py` |
| Audio transcription | Whisper-based transcription from video sources | `agents/vision-agent/video_understanding.py` |
| Frame analysis | GPT-4o multi-modal analysis of video keyframes | `agents/vision-agent/video_understanding.py` |
| Visual QA | Answer questions about images for fact-verification | `agents/vision-agent/visual_qa.py` |
| Image claim verification | Verify text claims against visual evidence | `agents/vision-agent/visual_qa.py` |
| Manipulation detection | Detect AI-generated or manipulated images | `agents/vision-agent/visual_qa.py` |

**Definition of Done:**
- [ ] Thumbnails auto-generated for every published article
- [ ] Social cards created for Twitter, Instagram, YouTube per article
- [ ] Video sources can be ingested, transcribed, and analyzed
- [ ] Visual fact-checking flags manipulated images

---

### Sprint 39–40: Real-Time Fact-Checking (Weeks 77–80)

**Sprint 39: Claim Extraction + Live Verification**

| Task | Description | File(s) |
|---|---|---|
| Claim extractor | LLM-based extraction of verifiable claims from text | `agents/fact-agent/claim_extractor.py` |
| Claim prioritization | Rank claims by verifiability and importance | `agents/fact-agent/claim_extractor.py` |
| Web search verifier | DuckDuckGo-based evidence gathering | `agents/fact-agent/live_verifier.py` |
| Knowledge base verifier | RAG-based verification against stored articles | `agents/fact-agent/live_verifier.py` |
| Official data verifier | Wikipedia/Wikidata entity verification | `agents/fact-agent/live_verifier.py` |
| LLM verdict engine | Evidence synthesis into verification verdicts | `agents/fact-agent/live_verifier.py` |

**Sprint 40: Evidence Scoring + Pipeline Integration**

| Task | Description | File(s) |
|---|---|---|
| Evidence scorer | Aggregate claim verdicts into overall fact-check grade | `agents/fact-agent/evidence_scorer.py` |
| Source reliability weights | Configurable reliability scores per source type | `agents/fact-agent/evidence_scorer.py` |
| Grade thresholds | A-F grading with editorial review flags | `agents/fact-agent/evidence_scorer.py` |
| Prompt templates | YAML configs for fact-checking prompts | `ai/prompts/templates/fact_checker.yaml` |
| Pipeline state | Add fact-check fields to PipelineState | `agents/orchestrator/state.py` |

**Definition of Done:**
- [ ] Every article gets a fact-check grade (A-F) before publishing
- [ ] Disputed claims trigger editorial review in moderation queue
- [ ] Live web search + knowledge base used for cross-referencing
- [ ] Fact-check scores visible in Control Center

---

### Sprint 41–42: Agent Self-Improvement (Weeks 81–84)

**Sprint 41: Performance Tracking + Prompt Evolution**

| Task | Description | File(s) |
|---|---|---|
| Performance tracker | Per-agent metrics: latency, quality, cost, tokens, errors | `ai/self_improve/performance_tracker.py` |
| Run recording | Record every agent invocation with full metadata | `ai/self_improve/performance_tracker.py` |
| Trend detection | Identify improving/degrading agents over time | `ai/self_improve/performance_tracker.py` |
| Prompt evolver | LLM-powered prompt improvement from performance data | `ai/self_improve/prompt_evolver.py` |
| Prompt registry | Version-controlled prompt variants with lineage tracking | `ai/self_improve/prompt_evolver.py` |

**Sprint 42: A/B Testing + Feedback Loop**

| Task | Description | File(s) |
|---|---|---|
| A/B test framework | Traffic splitting, result recording, statistical significance | `ai/self_improve/auto_tuner.py` |
| Auto-promotion | Winners automatically promoted after significance threshold | `ai/self_improve/auto_tuner.py` |
| Feedback loop controller | Full self-improvement orchestration cycle | `ai/self_improve/feedback_loop.py` |
| Cooldown system | Prevent over-evolution with cooldown periods | `ai/self_improve/auto_tuner.py` |
| Module exports | Clean API for the self-improvement system | `ai/self_improve/__init__.py` |

**Definition of Done:**
- [ ] Agent quality scores tracked across all pipeline runs
- [ ] Underperforming agents auto-evolve their prompts
- [ ] A/B tests run with statistical significance before promotion
- [ ] Self-improvement cycle runs without human intervention
- [ ] Prompt version history preserved with full lineage

**Tech Decisions:**
| Decision | Choice | Rationale |
|---|---|---|
| Image generation | GPT Image-1 (OpenAI) | High quality, API-compatible, no separate infra |
| Video analysis | GPT-4o multi-modal | Frame + audio analysis in one model |
| Transcription | Whisper-1 | Best accuracy for news audio |
| Fact-check search | DuckDuckGo + Wikipedia + RAG | Free, no API key needed, plus internal KB |
| Statistical testing | Welch's t-test (z-approximation) | Simple, appropriate for A/B with unequal variance |
| Prompt evolution | LLM-generated | Self-referential improvement, no manual tuning needed |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| LLM API costs spike with scale | High | High | Set per-pipeline cost budgets, cache embeddings, use cheaper models for non-critical agents |
| HeyGen API rate limits block video scale | Medium | High | Pre-render during off-peak, implement video queue with backpressure |
| Microservice migration breaks existing frontend | Medium | Medium | API contract tests, feature flags, gradual traffic migration |
| Solo developer bottleneck | High | High | Hire backend engineer by Sprint 9, mobile dev by Sprint 17 |
| Supabase free tier limits exceeded | Medium | Low | Upgrade to Pro ($25/mo) early, monitor usage |
| YouTube/social API policy changes | Low | High | Implement adapter pattern, swap providers without pipeline changes |
| SOC 2 audit cost ($20K–$50K) | Low | Medium | Budget from Phase 3 API revenue, defer if revenue < target |
| Kubernetes complexity for solo dev | Medium | Medium | Start with Docker Compose, graduate to K8s only when needed |

---

## Resource Requirements

### Engineering

| Phase | Duration | Engineers | Skills Needed |
|---|---|---|---|
| Phase 3 | 4 months | 1 | Python, FastAPI, Docker, Redis |
| Phase 4 | 3 months | 1–2 | Python, LLM APIs, LangGraph, pgvector |
| Phase 5 | 5 months | 2–3 | React Native, Terraform, ffmpeg, platform APIs |
| Phase 6 | 6 months | 3–5 | Full-stack, sales engineering, compliance |
| Phase 7 | 3 months | 2–3 | LLM multi-modal, prompt engineering, statistics, ffmpeg |

### Infrastructure Costs (Monthly)

| Phase | Cloud | APIs | Total |
|---|---|---|---|
| Phase 3 | $100 | $500 | $600 |
| Phase 4 | $200 | $1,500 | $1,700 |
| Phase 5 | $1,000 | $3,000 | $4,000 |
| Phase 6 | $5,000 | $10,000 | $15,000 |
| Phase 7 | $5,000 | $15,000 | $20,000 |

### Revenue Targets (Monthly)

| Milestone | Target MRR | Source |
|---|---|---|
| End Phase 3 (Month 4) | $3,000 | B2B API subscriptions |
| End Phase 4 (Month 6) | $10,000 | API + early premium |
| End Phase 5 (Month 10) | $50,000 | API + premium + ads |
| End Phase 6 (Month 18) | $200,000 | All revenue streams |
| End Phase 7 (Month 21) | $300,000 | All streams + premium AI features |

---

## Success Criteria

| Metric | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 |
|---|---|---|---|---|---|
| Services running independently | 7 | 7 | 7 | 7 | 7 |
| Agents operational | 5 | 10 | 10 | 10 | 15+ (multi-modal) |
| Articles/day | 100 | 300 | 500 | 1,000 | 1,500+ |
| Languages | 2 | 5 | 5 | 5+ | 5+ |
| API uptime | 99% | 99.5% | 99.9% | 99.99% | 99.99% |
| B2B clients | 5 | 15 | 30 | 50+ | 75+ |
| Monthly revenue | $3K | $10K | $50K | $200K+ | $300K+ |
| Platforms | Web | Web | Web + Mobile + YouTube + Telegram | All channels | All channels |
| Test coverage | 40% | 60% | 70% | 80% | 85% |
| Fact-check grade | — | — | — | — | A/B on 95% of articles |
| Agent self-improvement | — | — | — | — | Automated prompt evolution |
| Multi-modal coverage | — | — | — | — | Images + video analysis |
