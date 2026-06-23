"""
A.N.N. Article Service
Manages broadcast scripts — CRUD, persistent storage, RSS/Atom/JSON feeds, pipeline, and embeds.
"""

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy import desc

from config import get_settings
from database import init_db, AsyncSessionLocal, ScriptRow
from schemas import ScriptResponse, ScriptCreate, ArticleInput
from feeds import generate_rss, generate_atom, generate_json_feed
from pipeline import create_job, get_job, list_jobs, run_pipeline

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


# ── Pipeline ─────────────────────────────────────────────


class PipelineRequest(BaseModel):
    category: str = "general"
    query: str | None = None
    max_articles: int = 5


@app.post("/api/v1/pipeline/run")
async def pipeline_run(
    background_tasks: BackgroundTasks,
    request: PipelineRequest = PipelineRequest(),
    generate_media: bool = Query(False),
    source: str = Query("newsapi"),
):
    job = create_job()
    background_tasks.add_task(
        run_pipeline, job.job_id, request.category, request.query,
        request.max_articles, source, generate_media,
    )
    return {"job_id": job.job_id}


@app.get("/api/v1/pipeline/status/{job_id}")
async def pipeline_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress_pct": job.progress_pct,
        "scripts": job.scripts,
        "errors": job.errors,
    }


@app.get("/api/v1/pipeline/jobs")
async def pipeline_jobs(limit: int = Query(20, ge=1, le=50)):
    return list_jobs(limit)


# ── Single Article Processing ────────────────────────────

@app.post("/api/v1/process_news", response_model=ScriptResponse)
async def process_single_article(article: ArticleInput):
    from pipeline import process_article_through_llm
    import uuid

    result = await process_article_through_llm({
        "raw_text": article.raw_text,
        "source_name": article.source_name,
        "source_url": article.source_url,
        "category": article.category,
    })
    if not result:
        raise HTTPException(status_code=500, detail="Processing failed.")

    row = ScriptRow(
        id=str(uuid.uuid4())[:8],
        headline=result["headline"],
        english_script=result["english_script"],
        hindi_script=result.get("hindi_script", ""),
        category=result["category"],
        source_url=result.get("source_url", ""),
        word_count_en=len(result["english_script"].split()),
        word_count_hi=len(result.get("hindi_script", "").split()),
        estimated_duration_seconds=int((len(result["english_script"].split()) / 150) * 60),
    )
    async with AsyncSessionLocal() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return ScriptResponse.model_validate(row)


# ── Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
