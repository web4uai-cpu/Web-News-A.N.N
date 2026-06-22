# A.N.N. — Product Requirement Document

> **Version:** 1.0
> **Last Updated:** 2026-06-22
> **Status:** Active Development

---

## 1. Mission

Eliminate the human bottleneck in news production by building a fully autonomous, AI-powered news network that discovers, verifies, writes, produces, and distributes broadcast-ready news content at machine speed — 24/7, across languages and platforms.

---

## 2. Vision

A.N.N. becomes the world's first end-to-end autonomous news network where:

- **Zero human writers** are required for daily news production
- **10 specialized AI agents** collaborate in a pipeline to produce fact-checked, legally compliant, SEO-optimized, multi-language broadcast scripts
- **AI avatars** deliver news via generated video — indistinguishable from human anchors
- **Content distributes automatically** to web, mobile, YouTube, social media, Telegram, and WhatsApp
- **Enterprise clients** consume real-time news data via API for trading algorithms, news aggregators, and custom applications
- **The system learns** from engagement analytics to improve content quality over time

A.N.N. is not a tool for journalists — it **is** the journalist, the editor, the anchor, the producer, and the distribution network.

---

## 3. Target Audience

### 3.1 Primary: B2B Enterprise Clients

| Segment | Use Case | Value Proposition |
|---|---|---|
| **News Aggregators** | Ingest real-time JSON/RSS feeds into their platforms | Pre-verified, structured news data at sub-second latency |
| **Trading Firms & Fintech** | Feed financial news into algorithmic trading systems | Real-time market-moving events via WebSocket stream |
| **Media Companies** | White-label news content for their own channels | Multi-language broadcast scripts ready for air |
| **Developers** | Build news-powered applications using the API | Simple REST/WebSocket API with generous quotas |

**Interface:** Orbital Portal → Command Center, Developer API tab
**Monetization:** Tiered Stripe subscriptions (Starter / Pro / Enterprise) with API key quotas

### 3.2 Secondary: Social Media Creators

| Segment | Use Case | Value Proposition |
|---|---|---|
| **YouTube News Channels** | Automated daily news video uploads | Full pipeline: topic → script → avatar video → upload |
| **Instagram/TikTok Creators** | Short-form news clips for social feeds | Auto-formatted vertical video with captions |
| **Telegram/WhatsApp Channels** | Automated news blasts to subscribers | Text + media pushed directly to channel |
| **Automated News Pages** | Facebook/X pages running on autopilot | Scheduled posts with optimized timing |

**Interface:** Orbital Portal → Synthesis Engine, Social Auto-Pilot tabs
**Monetization:** Creator tier subscription (per-generation credits)

### 3.3 Tertiary: Direct Consumers

| Segment | Use Case | Value Proposition |
|---|---|---|
| **News Readers** | Consume AI-generated news on the website | Clean, ad-supported news feed with category filtering |
| **Multi-language Audience** | Read/listen in English or Hindi | Same story available in both languages instantly |

**Interface:** Public news website (`/news`)
**Monetization:** Display advertising (Google AdSense), sponsored content slots

---

## 4. Features

### 4.1 Data Acquisition Layer

| Feature | Description | Status |
|---|---|---|
| NewsAPI Integration | Ingest breaking news from 80,000+ sources | ✅ Built |
| GDELT Integration | Global geopolitical event monitoring | ✅ Built |
| AlphaVantage Integration | Real-time financial market data | ✅ Built |
| RSS/Atom Feed Ingestion | Custom RSS source subscriptions | 🔲 Planned |
| Government Feed Ingestion | Official government press releases | 🔲 Planned |
| Social Signal Detection | Trending topic detection from social platforms | 🔲 Planned |
| Reuters/AP Wire Feeds | Premium wire service integration | 🔲 Planned |

### 4.2 Multi-Agent AI Pipeline

| Agent | Function | Status |
|---|---|---|
| Discovery Agent | Source ingestion, deduplication, relevance scoring | 🟡 Partial (ingestion built, dedup planned) |
| Fact Verification Agent | Cross-reference claims, confidence scoring | ✅ Built (`fact_extractor.py`) |
| Legal Compliance Agent | Copyright, defamation, GDPR compliance | 🔲 Planned |
| News Writer Agent | Broadcast script generation with tone control | ✅ Built (`scriptwriter.py`) |
| SEO Agent | Keyword optimization, meta tags, structured data | 🔲 Planned |
| Translation Agent | Multi-language translation (EN → HI) | ✅ Built (`translator.py`) |
| Headline Generator | Click-worthy headline generation | ✅ Built (`headline_generator.py`) |
| Quality Critic Agent | Review and score script quality | ✅ Built (`critic.py`) |
| Avatar Producer Agent | Voice synthesis + video avatar rendering | ✅ Built (`elevenlabs_tts.py`, `heygen_video.py`) |
| Publishing Agent | Multi-channel content distribution | 🟡 Partial (social posters built) |

### 4.3 Content Production

| Feature | Description | Status |
|---|---|---|
| Broadcast Script Generation | EN + HI scripts with word counts and duration estimates | ✅ Built |
| ElevenLabs Voice Synthesis | AI voice clones for English and Hindi | ✅ Built |
| HeyGen Avatar Video | AI anchor video generation | ✅ Built |
| Thumbnail Generation | Auto-generated article thumbnails | 🔲 Planned |
| Short-form Video (Reels) | Vertical format for Instagram/TikTok | 🔲 Planned |

### 4.4 Distribution Channels

| Channel | Type | Status |
|---|---|---|
| Website (`/news`) | Public news reader with category navigation | ✅ Built |
| RSS/Atom Feeds | Standard syndication feeds | ✅ Built |
| Twitter/X | Auto-post headlines with links | ✅ Built |
| Facebook | Page posts with media | ✅ Built |
| Instagram | Feed posts via Graph API | ✅ Built |
| WebSocket Stream | Real-time push for B2B clients | ✅ Built |
| JSON API Feed | RESTful B2B data access | ✅ Built |
| YouTube | Automated video uploads | 🔲 Planned |
| Telegram | Channel message blasts | 🔲 Planned |
| WhatsApp Channels | Broadcast list distribution | 🔲 Planned |
| Mobile Push | Native app notifications | 🔲 Planned |

### 4.5 Enterprise & Monetization

| Feature | Description | Status |
|---|---|---|
| Supabase Auth | User registration, login, password reset | ✅ Built |
| Orbital Portal | B2B dashboard with quota monitoring | ✅ Built |
| Stripe Billing | Subscription checkout and webhook handling | ✅ Built |
| API Key Management | Generate, rotate, and revoke `ann_sk_*` keys | ✅ Built |
| Tiered Quotas | Starter (10K), Pro (50K), Enterprise (100K) req/month | ✅ Built |
| Webhook Delivery | Push new articles to client endpoints | ✅ Built |
| Ad Slots | Display advertising placement on public site | 🟡 Placeholder |

### 4.6 Platform & Operations

| Feature | Description | Status |
|---|---|---|
| Admin Dashboard | Pipeline control, stats, logs, API key settings | ✅ Built |
| Celery Task Queue | Async pipeline execution via Redis | ✅ Built |
| Prometheus Metrics | Request latency, error rates, queue depth | ✅ Built |
| Grafana Dashboards | Visual monitoring | ✅ Built |
| Docker Compose | Full-stack local deployment | ✅ Built |
| Kubernetes Manifests | Production orchestration | 🟡 Partial |
| CI/CD Pipeline | Automated test + deploy | 🔲 Planned |
| Next.js Frontend | Modern React-based web UI | ✅ Built |

---

## 5. Success Metrics

### 5.1 Product Metrics

| Metric | Target (6 months) | Target (12 months) |
|---|---|---|
| Articles generated per day | 100 | 500 |
| Average pipeline latency (article → published) | < 5 minutes | < 2 minutes |
| Fact verification accuracy | > 90% | > 95% |
| Languages supported | 2 (EN, HI) | 5 (+ AR, ES, FR) |
| Video generations per day | 20 | 100 |

### 5.2 Business Metrics

| Metric | Target (6 months) | Target (12 months) |
|---|---|---|
| B2B API clients | 10 | 50 |
| Monthly recurring revenue (MRR) | $5,000 | $25,000 |
| Creator tier subscribers | 50 | 500 |
| Monthly API requests served | 500K | 5M |
| Website monthly unique visitors | 50K | 500K |

### 5.3 Engagement Metrics

| Metric | Target |
|---|---|
| Average time on site | > 3 minutes |
| News feed CTR (click-through rate) | > 8% |
| Video average watch time | > 60% of duration |
| Social media post engagement rate | > 3% |
| B2B API uptime SLA | 99.9% |

### 5.4 Quality Metrics

| Metric | Target |
|---|---|
| Duplicate article rate | < 2% |
| Legal compliance violations | 0 |
| Script quality score (critic agent) | > 8/10 average |
| Translation accuracy (human eval sample) | > 90% |

---

## 6. Roadmap

### Phase 1: Foundation (Completed ✅)

> Core pipeline operational with monolith architecture

- [x] FastAPI backend with REST API
- [x] NewsAPI, GDELT, AlphaVantage ingestion
- [x] AI agent pipeline (fact extraction → scriptwriting → translation → headlines)
- [x] ElevenLabs TTS + HeyGen video generation
- [x] Social media auto-posting (Twitter, Facebook, Instagram)
- [x] Supabase Auth + Stripe billing
- [x] B2B Orbital Portal with API key management
- [x] Public news website with category filtering
- [x] Celery + Redis async task queue
- [x] Docker Compose deployment
- [x] Prometheus + Grafana monitoring

### Phase 2: Modern Frontend (Completed ✅)

> Rebuild frontend with production-grade React stack

- [x] Next.js 16 + TypeScript + TailwindCSS
- [x] Zustand state management + React Query data fetching
- [x] Framer Motion animations
- [x] Dashboard page (pipeline control, stats, scripts, logs)
- [x] News page (ticker, hero, feed grid, reader modal)
- [x] Portal page (Supabase auth, tabs: overview, API, social, studio)
- [x] Toast notification system
- [x] Typed API client for backend

### Phase 3: Microservice Migration (Current 🟡)

> Decompose monolith into independently deployable services

- [x] Microservice directory structure scaffolded
- [ ] API Gateway service (routing, rate limiting, auth validation)
- [ ] Auth Service (extract from monolith → standalone JWT/Supabase service)
- [ ] Article Service (CRUD, search, feeds)
- [ ] Video Service (TTS + avatar generation)
- [ ] Notification Service (social posting, webhooks, push)
- [ ] Analytics Service (engagement tracking, agent scoring)
- [ ] Search Service (full-text + semantic/vector search)
- [ ] Inter-service communication (Redis Streams or gRPC)
- [ ] Per-service Dockerfiles and health checks
- [ ] Kubernetes deployment manifests

### Phase 4: Advanced AI Agents (Planned 🔲)

> Upgrade from simple LLM calls to autonomous, memory-equipped agents

- [ ] Agent orchestrator with DAG-based pipeline (LangGraph or custom)
- [ ] Discovery Agent: smart deduplication with semantic similarity
- [ ] Legal Compliance Agent: copyright + defamation + GDPR scanning
- [ ] SEO Agent: keyword research, meta tags, schema.org markup
- [ ] RAG pipeline: vector embeddings for grounded fact-checking
- [ ] Agent memory: cross-session context and learning
- [ ] Prompt library with versioning and A/B testing
- [ ] Agent performance scoring and auto-tuning

### Phase 5: Scale & Distribution (Planned 🔲)

> Expand to new channels, languages, and markets

- [ ] YouTube automated upload pipeline
- [ ] Telegram bot + channel distribution
- [ ] WhatsApp Business API integration
- [ ] React Native mobile app (iOS + Android)
- [ ] 3 additional languages (Arabic, Spanish, French)
- [ ] Short-form vertical video (Reels/Shorts/TikTok)
- [ ] Push notifications (web + mobile)
- [ ] Terraform IaC for cloud provisioning
- [ ] CDN for media asset delivery
- [ ] Multi-region deployment

### Phase 6: Enterprise & Revenue (Planned 🔲)

> Maximize revenue and enterprise adoption

- [ ] Admin dashboard for internal ops team
- [ ] Content moderation queue with human-in-the-loop
- [ ] White-label API for media companies
- [ ] Advanced analytics dashboard (Recharts)
- [ ] A/B testing for headlines and content formats
- [ ] Programmatic ad integration (Google AdSense + direct deals)
- [ ] Enterprise SLA tiers with dedicated support
- [ ] SOC 2 compliance and security audit
- [ ] Public status page and uptime monitoring

---

## Appendix

### A. System Architecture

```
Data Sources → Discovery Agent → Fact Agent → Legal Agent
    → Rewrite Agent → SEO Agent → Translation Agent
    → Avatar Agent → Publishing Agent
    → Analytics → Feedback Loop → Agent Learning
```

### B. API Surface

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System health and uptime |
| `/api/v1/scripts` | GET | List generated broadcast scripts |
| `/api/v1/process_news` | POST | Process a single article through the pipeline |
| `/api/v1/pipeline/run` | POST | Trigger full autonomous pipeline |
| `/api/v1/pipeline/status/:id` | GET | Check pipeline job progress |
| `/api/v1/ingest/newsapi` | POST | Trigger NewsAPI ingestion |
| `/api/v1/ingest/financial` | POST | Trigger financial data ingestion |
| `/api/v1/media/generate_audio` | POST | Generate TTS audio for a script |
| `/api/v1/b2b/feed/json` | GET | Premium B2B JSON feed (API key required) |
| `/api/v1/b2b/checkout` | POST | Stripe subscription checkout |
| `/api/v1/admin/settings` | GET/POST | System API key management |
| `/api/v1/admin/clients` | POST | Create B2B client |
| `/feed/rss` | GET | Public RSS feed |
| `/feed/atom` | GET | Public Atom feed |
| `/ws/breaking-news` | WS | Real-time WebSocket stream |

### C. Monetization Tiers

| Tier | Price/mo | API Requests | WebSocket | Video Generations | Support |
|---|---|---|---|---|---|
| **Starter** | $49 | 10,000 | — | — | Email |
| **Pro** | $199 | 50,000 | ✅ | 50/mo | Priority |
| **Enterprise** | $499 | 100,000 | ✅ | Unlimited | Dedicated |
| **Creator** | $29 | — | — | 30/mo | Community |
