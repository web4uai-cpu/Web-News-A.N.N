"""System routes: health check and legacy static pages."""

import os
import time

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from config import get_settings
from core import runtime
from models.schemas import HealthResponse
from services.queue_manager import queue_manager

router = APIRouter()
settings = get_settings()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="A.N.N. Editorial Agent is running. Antigravity is engaged. 🛰️",
        version=settings.app_version,
        uptime_seconds=round(time.time() - runtime.START_TIME, 1),
        active_jobs=queue_manager.active_count,
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
