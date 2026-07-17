"""
A.N.N. (AI News Network) - FastAPI Application Factory
======================================================
Modular monolith entry point: middleware, lifespan, and router mounting only.
Domain logic lives in backend/routers/*; shared singletons in core/runtime.py.
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# ── Ensure backend is on path ──────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from config import get_settings
from utils.logger import setup_logging, get_logger
from utils.rate_limiter import rate_limiter

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# ── Setup ──────────────────────────────────────────────
setup_logging()
log = get_logger("main")
settings = get_settings()

from core import runtime
from models.schemas import BroadcastScript
from services.realtime import listen_to_redis_broadcasts
from routers import ALL_ROUTERS


# ── Lifespan ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    log.info(
        "ann_starting",
        version=settings.app_version,
        model=settings.llm_model,
    )

    # Initialize cache layer
    try:
        from fastapi_cache.backends.redis import RedisBackend
        from redis import asyncio as aioredis
        if os.getenv("REDIS_URL"):
            redis = aioredis.from_url(os.getenv("REDIS_URL"), encoding="utf8", decode_responses=True)
            FastAPICache.init(RedisBackend(redis), prefix="ann-cache")
            log.info("cache_initialized", backend="redis")
        else:
            FastAPICache.init(InMemoryBackend(), prefix="ann-cache")
            log.info("cache_initialized", backend="in-memory")
    except Exception as e:
        FastAPICache.init(InMemoryBackend(), prefix="ann-cache")
        log.warning("cache_fallback", error=str(e))

    # Initialize SQL Database
    from models.b2b_database import init_db, load_all_scripts
    await init_db()
    log.info("database_initialized")

    # Load persisted scripts into memory
    saved_scripts = await load_all_scripts()
    for s in saved_scripts:
        runtime.script_store[s["id"]] = BroadcastScript(**s)
    log.info("scripts_loaded_from_db", count=len(saved_scripts))

    # Register rate limiters
    rate_limiter.register("llm", rpm=settings.llm_rpm)
    rate_limiter.register("newsapi", rpm=settings.news_api_rpm)
    rate_limiter.register("elevenlabs", rpm=settings.elevenlabs_rpm)
    rate_limiter.register("heygen", rpm=settings.heygen_rpm)

    # Create output directories
    os.makedirs(os.path.join(os.path.dirname(__file__), "output", "audio"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "output", "video"), exist_ok=True)

    # Redis pub/sub listener bridging Celery workers → WebSockets
    listener_task = asyncio.create_task(listen_to_redis_broadcasts())

    log.info("ann_ready", msg="All systems nominal. Enterprise Architecture is engaged. 🚀")
    yield

    listener_task.cancel()
    log.info("ann_shutting_down")


# ── FastAPI App ────────────────────────────────────────
app = FastAPI(
    title="A.N.N. — AI News Network",
    description=(
        "Autonomous multi-agent AI news network. "
        "Ingests news, extracts facts, generates original broadcast scripts, "
        "and produces AI avatar video content."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS — explicit allowlist + Vercel preview regex (configure CORS_ORIGINS / CORS_ORIGIN_REGEX)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── API version header ─────────────────────────────────
@app.middleware("http")
async def add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = f"v1 ({settings.app_version})"
    return response


# ── Metrics Instrumentation ────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
except ImportError:
    pass

# Serve the legacy frontend dashboard + public news assets
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

PUBLIC_DIR = os.path.join(FRONTEND_DIR, "public")
if os.path.exists(PUBLIC_DIR):
    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

# ── Routers ────────────────────────────────────────────
for router in ALL_ROUTERS:
    app.include_router(router)


# ══════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
