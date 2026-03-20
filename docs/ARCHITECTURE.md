# 🏗️ A.N.N. System Architecture

The **AI News Network (A.N.N.)** operates through a highly decoupled, event-driven pipeline. This document maps out exactly how data flows from ingestion to broadcast.

## 1. Data Ingestion Layer (`backend/ingestion/`)
A.N.N. acts as an aggregate crawler using external APIs. The ingestion layer securely fetches raw news using the following modules:
* `newsapi_source.py`: Scrapes general, business, and tech news from NewsAPI.
* `alphavantage_source.py`: Focuses strictly on financial tickers and global markets.
* `gdelt_source.py`: Crawls global socio-political events and breaking geographic incidents.

*All scrapers enforce strict rate limiting using `utils/rate_limiter.py` to prevent API bans.*

## 2. Multi-Agent Processing Pipeline (`backend/agents/`)
Whenever a raw article is fetched, it is routed through a series of intelligent LLM agents.
1. **FactExtractorAgent**: Analyzes the raw article for verifiable, mathematical, and objective facts. **It strips all original prose** to ensure A.N.N. is legally protected from copyright infringement.
2. **ScriptwriterAgent**: Takes the extracted facts and generates a brand-new, original broadcast script using professional news-anchor tonality.
3. **CriticAgent**: Evaluates the script for hallucinations or sensationalism. If the script fails, the `ScriptwriterAgent` is forced into a rewrite loop.
4. **HeadlineGeneratorAgent**: Crafts an AP-style breaking news headline.
5. **TranslatorAgent**: Translates the final script into Hindi (and maps out Arabic/Spanish/French logic for future scale).

## 3. Media Generation (`backend/media/`)
Once the editorial process completes successfully, the pipeline triggers the Media layers:
* **Audio**: `elevenlabs_tts.py` invokes ElevenLabs voice cloning to generate ultra-realistic English and Hindi voiceovers.
* **Video**: `heygen_video.py` transmits the scripts to HeyGen to synthesize artificial human anchors lip-syncing the broadcast.

## 4. Distribution, Syndication & Streaming (`backend/feeds/` & `backend/social/` & `backend/main.py`)
The final `BroadcastScript` entity is simultaneously blasted out using world-class distribution techniques:
* **High-Performance WebSockets**: `main.py` utilizes FastAPI `WebSocket` routing to simultaneously push the generated `BroadcastScript` direct to the `frontend/public/news.html` dashboard natively. Browsers auto-render breaking news without needing to reload the webpage.
* **Supabase Cloud Sync**: `supabase_client.py` pushes the DB record to a Supabase Postgres instance for worldwide Edge CDN delivery.
* **Social Media Automations**: `social_scheduler.py` triggers `instagram_poster.py` (which uses Pillow to generate a branded 1080x1080 graphic card), `facebook_poster.py`, and `twitter_poster.py`.
* **RSS / Atom Feeds**: The scripts are automatically served as statically-parseable XML objects to `http://localhost:8000/feed/rss` and `/feed/atom`.
* **Stripe Revenue & Webhooks**: The system natively exposes Checkout mechanisms in `backend/services/billing.py`. Clients pay via Stripe -> Stripe Webhook hits A.N.N. -> Auto-generates an enterprise API Key via SQLAlchemy Alembic Migrations -> Dispatches raw JSON news to their own servers via `webhook.py`.
