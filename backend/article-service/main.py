"""
A.N.N. Article Service
Manages broadcast scripts — CRUD, persistent storage, RSS/Atom/JSON feeds, and embeds.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.future import select
from sqlalchemy import desc

from config import get_settings
from database import init_db, AsyncSessionLocal, ScriptRow
from schemas import ScriptResponse, ScriptCreate, ArticleInput
from feeds import generate_rss, generate_atom, generate_json_feed

settings = get_settings()
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="A.N.N. Article Service",
    description="Broadcast script storage, retrieval, and syndication feeds.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"service": "article-service", "status": "healthy", "uptime_seconds": round(time.time() - START_TIME, 1)}


# ── Script CRUD ───────────────────────────────────────────

@app.get("/api/v1/scripts", response_model=list[ScriptResponse])
async def list_scripts(limit: int = Query(20, ge=1, le=100)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ScriptRow).order_by(desc(ScriptRow.created_at)).limit(limit)
        )
        rows = result.scalars().all()
    return [ScriptResponse.model_validate(r) for r in rows]


@app.get("/api/v1/scripts/latest")
async def latest_headlines(limit: int = Query(10, ge=1, le=30)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ScriptRow).order_by(desc(ScriptRow.created_at)).limit(limit)
        )
        rows = result.scalars().all()
    return [{"id": r.id, "headline": r.headline, "category": r.category, "created_at": r.created_at} for r in rows]


@app.get("/api/v1/scripts/{script_id}", response_model=ScriptResponse)
async def get_script(script_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ScriptRow).where(ScriptRow.id == script_id))
        row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="Script not found.")
    return ScriptResponse.model_validate(row)


@app.post("/api/v1/scripts", response_model=ScriptResponse)
async def create_script(data: ScriptCreate):
    row = ScriptRow(
        headline=data.headline,
        english_script=data.english_script,
        hindi_script=data.hindi_script,
        translations=data.translations,
        category=data.category,
        source_url=data.source_url,
        word_count_en=len(data.english_script.split()),
        word_count_hi=len(data.hindi_script.split()) if data.hindi_script else 0,
        estimated_duration_seconds=int((len(data.english_script.split()) / 150) * 60),
    )
    async with AsyncSessionLocal() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return ScriptResponse.model_validate(row)


# ── Syndication Feeds ─────────────────────────────────────

async def _get_scripts_dicts(category: str | None, limit: int) -> list[dict]:
    async with AsyncSessionLocal() as session:
        q = select(ScriptRow).order_by(desc(ScriptRow.created_at))
        if category:
            q = q.where(ScriptRow.category == category)
        result = await session.execute(q.limit(limit))
        rows = result.scalars().all()
    return [
        {
            "id": r.id, "headline": r.headline, "english_script": r.english_script,
            "hindi_script": r.hindi_script, "category": r.category,
            "word_count_en": r.word_count_en, "word_count_hi": r.word_count_hi,
            "estimated_duration_seconds": r.estimated_duration_seconds,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@app.get("/feed/rss")
async def rss_feed(category: str | None = Query(None), limit: int = Query(20, ge=1, le=50)):
    scripts = await _get_scripts_dicts(category, limit)
    xml = generate_rss(scripts, settings.public_url, category)
    return Response(content=xml, media_type="application/rss+xml")


@app.get("/feed/atom")
async def atom_feed(category: str | None = Query(None), limit: int = Query(20, ge=1, le=50)):
    scripts = await _get_scripts_dicts(category, limit)
    xml = generate_atom(scripts, settings.public_url, category)
    return Response(content=xml, media_type="application/atom+xml")


@app.get("/feed/json")
async def json_feed(category: str | None = Query(None), limit: int = Query(20, ge=1, le=50)):
    scripts = await _get_scripts_dicts(category, limit)
    return generate_json_feed(scripts, settings.public_url, category)


@app.get("/api/v1/b2b/feed/json")
async def b2b_json_feed(category: str | None = Query(None), limit: int = Query(20, ge=1, le=50)):
    scripts = await _get_scripts_dicts(category, limit)
    return generate_json_feed(scripts, settings.public_url, category)


# ── Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
