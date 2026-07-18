"""System routes: health check and legacy static pages."""

import os
import time

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from config import get_settings
from core import runtime
from models.schemas import HealthResponse
from services.queue_manager import queue_manager
from utils.logger import get_logger

router = APIRouter()
settings = get_settings()
log = get_logger("system")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")


async def _redis_health() -> dict:
    """Ping Redis if configured; report disabled when no REDIS_URL is set."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return {"status": "disabled"}
    try:
        from redis import asyncio as aioredis
        client = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
        try:
            await client.ping()
            return {"status": "healthy"}
        finally:
            await client.close()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _collect_service_health() -> dict:
    from models.b2b_database import check_db_health
    return {
        "database": await check_db_health(),
        "redis": await _redis_health(),
    }


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Liveness + dependency status. Always returns 200 so the platform health
    probe passes on boot; per-dependency status is reported in the body.
    """
    services = await _collect_service_health()
    return HealthResponse(
        status="A.N.N. Editorial Agent is running. Antigravity is engaged. 🛰️",
        version=settings.app_version,
        uptime_seconds=round(time.time() - runtime.START_TIME, 1),
        active_jobs=queue_manager.active_count,
        services=services,
    )


@router.get("/health/ready", tags=["System"])
async def readiness_check():
    """
    Readiness probe: 503 if the primary datastore (Postgres) is unreachable,
    so orchestrators can hold traffic until dependencies are live.
    """
    services = await _collect_service_health()
    ready = services["database"].get("status") == "healthy"
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"ready": ready, "services": services},
    )


@router.get("/", tags=["Dashboard"])
async def serve_dashboard():
    """Serve the A.N.N. Admin Dashboard."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "A.N.N. API is running. Dashboard not found — use /docs for API explorer."}


@router.get("/news", response_class=HTMLResponse, tags=["Web Interface"])
async def read_news_frontend():
    """Serves the beautifully monetized public-facing news feed with WebSockets."""
    file_path = os.path.join(FRONTEND_DIR, "public", "news.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: Public news feed not found</h1>"


@router.get("/portal", response_class=HTMLResponse, tags=["Web Interface"])
async def read_b2b_portal():
    """Serves the isolated B2B Client Portal for Enterprise SaaS customers."""
    file_path = os.path.join(FRONTEND_DIR, "public", "portal.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: B2B portal not found</h1>"
