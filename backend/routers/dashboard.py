"""Dashboard metrics endpoints (real data from the DB + system stats)."""

import os

from fastapi import APIRouter, Query

from config import get_settings
from core import runtime

router = APIRouter()
settings = get_settings()


@router.get("/api/v1/dashboard/agents", tags=["Dashboard"])
async def get_agent_metrics():
    """Real agent performance metrics from database."""
    from models.b2b_database import get_agent_stats
    stats = await get_agent_stats()
    if not stats:
        return [
            {"name": n, "shortName": s, "tasks_completed": 0, "avg_latency": "--", "status": "idle", "last_run": "--"}
            for n, s in [
                ("Discovery Agent", "DSC"), ("Fact Extractor", "FCT"), ("Scriptwriter", "SCR"),
                ("Critic Agent", "CRT"), ("Headline Gen", "HDL"), ("Translator", "TRN"),
                ("SEO Agent", "SEO"), ("Avatar Producer", "AVT"), ("Publisher", "PUB"), ("Legal Agent", "LGL"),
            ]
        ]
    return stats


@router.get("/api/v1/dashboard/throughput", tags=["Dashboard"])
async def get_throughput_metrics():
    """Real news throughput data from script creation timestamps."""
    from models.b2b_database import get_throughput_stats
    return await get_throughput_stats()


@router.get("/api/v1/dashboard/revenue", tags=["Dashboard"])
async def get_revenue_metrics():
    """Real revenue / B2B client data from database."""
    from models.b2b_database import get_revenue_stats
    return await get_revenue_stats()


@router.get("/api/v1/dashboard/media-jobs", tags=["Dashboard"])
async def get_media_jobs_list(limit: int = Query(20, ge=1, le=50)):
    """Real media production job statuses."""
    from models.b2b_database import get_media_jobs
    return await get_media_jobs(limit)


@router.get("/api/v1/dashboard/system", tags=["Dashboard"])
async def get_system_metrics():
    """Real system metrics — queue health, connections, memory."""
    import psutil
    process = psutil.Process()
    mem = process.memory_info()

    redis_status = "connected" if os.getenv("REDIS_URL") else "not_configured"
    celery_status = "connected" if os.getenv("REDIS_URL") else "not_configured"

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_used_mb": round(mem.rss / 1024 / 1024, 1),
        "memory_percent": round(process.memory_percent(), 1),
        "disk_usage_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent,
        "redis_status": redis_status,
        "celery_status": celery_status,
        "scripts_in_memory": len(runtime.script_store),
        "social_platforms": runtime.social_scheduler.enabled_platforms,
        "social_auto_post": settings.social_auto_post,
    }
