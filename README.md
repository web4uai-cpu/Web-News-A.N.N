# 🎙️ A.N.N. — AI News Network

**A.N.N.** is an entirely autonomous, enterprise-grade AI news broadcasting platform. It operates 24/7 without human intervention, ingesting global news from multiple sources (NewsAPI, AlphaVantage, GDELT), utilizing advanced Multi-Agent systems to legally rewrite and verify stories, translating content into multiple languages (English and Hindi), generating AI Avatar videos, and syndicating the final output across the open web and social media.

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+
- A configured `.env` file containing your API keys (LLM, Supabase, Socials, etc.)

### 2. Installation
Navigate into the `backend/` directory and install the exact Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

*(Note: The system utilizes `fastapi-cache2[redis]`, `SQLAlchemy`, and `asyncpg` for enterprise latency routing. An active PostgreSQL or local SQLite database is required).*

### 3. Environment Variables
Copy `.env.example` to `.env` inside the `backend/` folder and populate your keys:
```bash
cp .env.example .env
```
Ensure your `LLM_API_KEY`, `SUPABASE_URL`, and `DATABASE_URL` are strictly configured.

### 4. Running the Platform
Start the FastAPI server. It will automatically initialize the database schema and engage the pipelines on boot.

```bash
python main.py
```
Or run directly via Uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **Dashboard / Frontend:** `http://localhost:8000/`
- **Public News App:** `http://localhost:8000/news`
- **Swagger API Explorer:** `http://localhost:8000/docs`

---

## 🏗️ Technology Stack & Integrations
- **Backend Frame**: FastAPI (Python)
- **Database**: PostgreSQL (Supabase Edge) & local SQLite fallback
- **Agents**: LLM-driven Multi-Agent Architecture (Fact Extractor, Critic, Writer)
- **Media**: ElevenLabs (Audio TTS), HeyGen (Video AI Avatars), Pillow (Automated Graphic Cards)
- **Distribution Systems**:
    - **Cloud**: Supabase REST `upsert` synchronization.
    - **Syndication**: RSS 2.0, Atom 1.0, and JSON Feed 1.1 Feeds.
    - **Social Media**: Full Meta Graph integration (Instagram Cards + Facebook Posts) & X/Twitter v2 integration.
    - **Enterprise**: B2B PostgreSQL-backed Webhook Push Delivery.

## 📖 Deep Documentation
For a deep-dive into how the A.N.N. internal systems communicate, read the [Architecture Guide](./docs/ARCHITECTURE.md). For testing all internal and public APIs, import the [API Endpoints Collection](./docs/api_endpoints.json) into Postman or Insomnia.
