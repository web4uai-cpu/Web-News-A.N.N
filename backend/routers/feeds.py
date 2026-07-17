"""Syndication feeds (RSS/Atom/JSON), B2B commercial feed, and embeddable widgets."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache

from config import get_settings
from core import runtime
from feeds.atom_feed import generate_atom_feed
from feeds.embed_widget import generate_feed_widget_js, generate_ticker_widget_js
from feeds.rss_feed import generate_rss_feed
from services.auth import verify_b2b_api_key
from utils.logger import get_logger

router = APIRouter()
log = get_logger("feeds_router")
settings = get_settings()


@router.get("/feed/rss", tags=["Feeds"])
async def rss_feed(
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50),
):
    """RSS 2.0 feed — subscribe from any news reader or aggregator."""
    scripts = runtime.sorted_scripts()
    if category:
        scripts = [s for s in scripts if s.category.value == category]
    xml = generate_rss_feed(
        scripts[:limit], base_url=settings.public_url, category=category,
    )
    return JSONResponse(content=xml, media_type="application/rss+xml")


@router.get("/feed/atom", tags=["Feeds"])
async def atom_feed(
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50),
):
    """Atom 1.0 feed — modern feed standard for readers and aggregators."""
    scripts = runtime.sorted_scripts()
    if category:
        scripts = [s for s in scripts if s.category.value == category]
    xml = generate_atom_feed(
        scripts[:limit], base_url=settings.public_url, category=category,
    )
    return JSONResponse(content=xml, media_type="application/atom+xml")


@router.get("/feed/json", tags=["Feeds"])
@cache(expire=300)
async def json_feed(
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50),
):
    """JSON Feed 1.1 — developer-friendly feed format."""
    scripts = runtime.sorted_scripts()
    if category:
        scripts = [s for s in scripts if s.category.value == category]
    items = [
        {
            "id": s.id,
            "title": s.headline,
            "url": f"{settings.public_url}/news#script-{s.id}",
            "content_text": s.english_script,
            "content_hindi": s.hindi_script,
            "summary": s.english_script.replace('[PAUSE]', '')[:300],
            "date_published": s.created_at.isoformat(),
            "tags": [s.category.value],
            "_ann": {
                "word_count_en": s.word_count_en,
                "word_count_hi": s.word_count_hi,
                "duration_seconds": s.estimated_duration_seconds,
            },
        }
        for s in scripts[:limit]
    ]
    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "A.N.N. — AI News Network",
        "home_page_url": f"{settings.public_url}/news",
        "feed_url": f"{settings.public_url}/feed/json",
        "description": "AI-powered autonomous news broadcasts",
        "items": items,
    }


@router.get("/api/v1/b2b/feed/json", tags=["Feeds (B2B Commercial)"])
async def b2b_json_feed(
    client: dict = Depends(verify_b2b_api_key),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Premium B2B Feed — Commercial use of A.N.N. translated scripts.
    Requires Enterprise API Key (Header: X-ANN-API-Key).
    """
    log.info("b2b_feed_accessed", client_name=client["name"], category=category)
    # Simply reuse the public function logic internally
    return await json_feed(category=category, limit=limit)


# ── Embeddable Widgets ─────────────────────────────────

@router.get("/embed/ticker.js", tags=["Embed Widgets"])
async def embed_ticker():
    """Embeddable breaking-news ticker widget. Usage: <script src='/embed/ticker.js'></script><div id='ann-ticker'></div>"""
    js = generate_ticker_widget_js(base_url=settings.public_url)
    return JSONResponse(content=js, media_type="application/javascript")


@router.get("/embed/feed.js", tags=["Embed Widgets"])
async def embed_feed():
    """Embeddable news feed card widget. Usage: <script src='/embed/feed.js'></script><div id='ann-feed'></div>"""
    js = generate_feed_widget_js(base_url=settings.public_url)
    return JSONResponse(content=js, media_type="application/javascript")
