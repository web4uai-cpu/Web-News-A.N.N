"""
A.N.N. Search Service
Full-text search across broadcast scripts with category filtering and auto-suggest.
"""

import time
from contextlib import asynccontextmanager

import os

from fastapi import FastAPI, Query as Q, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy import desc, or_

from config import get_settings
from database import init_db, AsyncSessionLocal, SearchEntry

settings = get_settings()
START_TIME = time.time()


class IndexRequest(BaseModel):
    id: str
    headline: str
    content: str
    category: str = "general"
    word_count: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="A.N.N. Search Service",
    description="Full-text search across broadcast scripts.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"service": "search-service", "status": "healthy", "uptime_seconds": round(time.time() - START_TIME, 1)}


@app.get("/api/v1/search")
async def search(
    q: str = Q(..., min_length=1, description="Search query"),
    category: str | None = Q(None),
    limit: int = Q(20, ge=1, le=100),
):
    async with AsyncSessionLocal() as session:
        query = select(SearchEntry).where(
            or_(
                SearchEntry.headline.ilike(f"%{q}%"),
                SearchEntry.content.ilike(f"%{q}%"),
            )
        )
        if category:
            query = query.where(SearchEntry.category == category)
        query = query.order_by(desc(SearchEntry.created_at)).limit(limit)

        result = await session.execute(query)
        rows = result.scalars().all()

    return {
        "query": q,
        "total": len(rows),
        "results": [
            {
                "id": r.id,
                "headline": r.headline,
                "category": r.category,
                "word_count": r.word_count,
                "snippet": _snippet(r.content, q),
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@app.get("/api/v1/search/suggest")
async def suggest(q: str = Q(..., min_length=2), limit: int = Q(5, ge=1, le=10)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SearchEntry.headline)
            .where(SearchEntry.headline.ilike(f"%{q}%"))
            .order_by(desc(SearchEntry.created_at))
            .limit(limit)
        )
        headlines = result.scalars().all()
    return {"suggestions": headlines}


@app.post("/api/v1/search/index")
async def index_document(doc: IndexRequest):
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(SearchEntry).where(SearchEntry.id == doc.id))
        row = existing.scalars().first()
        if row:
            row.headline = doc.headline
            row.content = doc.content
            row.category = doc.category
            row.word_count = doc.word_count
        else:
            session.add(SearchEntry(
                id=doc.id,
                headline=doc.headline,
                content=doc.content,
                category=doc.category,
                word_count=doc.word_count,
            ))
        await session.commit()
    return {"status": "indexed", "id": doc.id}


@app.post("/api/v1/search/bulk-index")
async def bulk_index(docs: list[IndexRequest]):
    async with AsyncSessionLocal() as session:
        for doc in docs:
            existing = await session.execute(select(SearchEntry).where(SearchEntry.id == doc.id))
            row = existing.scalars().first()
            if row:
                row.headline = doc.headline
                row.content = doc.content
                row.category = doc.category
                row.word_count = doc.word_count
            else:
                session.add(SearchEntry(
                    id=doc.id, headline=doc.headline, content=doc.content,
                    category=doc.category, word_count=doc.word_count,
                ))
        await session.commit()
    return {"status": "indexed", "count": len(docs)}


def _snippet(content: str, query: str, context_chars: int = 150) -> str:
    lower = content.lower()
    pos = lower.find(query.lower())
    if pos == -1:
        return content[:context_chars * 2] + "..."
    start = max(0, pos - context_chars)
    end = min(len(content), pos + len(query) + context_chars)
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet += "..."
    return snippet


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
