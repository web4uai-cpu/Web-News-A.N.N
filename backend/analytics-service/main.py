"""
A.N.N. Analytics Service
Event tracking, engagement metrics, agent performance scoring, and dashboard data.
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy import func, desc

from config import get_settings
from database import (
    init_db, AsyncSessionLocal, AnalyticsEvent, AgentMetric,
    BroadcastScriptRow, AgentMetricDashboard, MediaJobRow, ClientAPIKey,
)

settings = get_settings()
START_TIME = time.time()


class EventCreate(BaseModel):
    event_type: str
    entity_id: str = ""
    entity_type: str = ""
    client_id: str = ""
    metadata: dict = {}
    value: float = 0.0


class AgentMetricCreate(BaseModel):
    agent_name: str
    pipeline_run_id: str = ""
    latency_ms: int = 0
    success: bool = True
    tokens_used: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="A.N.N. Analytics Service",
    description="Event tracking, engagement metrics, and agent performance scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"service": "analytics-service", "status": "healthy", "uptime_seconds": round(time.time() - START_TIME, 1)}


# ── Event Tracking ────────────────────────────────────────

@app.post("/api/v1/analytics/events")
async def track_event(event: EventCreate):
    async with AsyncSessionLocal() as session:
        row = AnalyticsEvent(
            event_type=event.event_type,
            entity_id=event.entity_id,
            entity_type=event.entity_type,
            client_id=event.client_id,
            event_metadata=event.metadata,
            value=event.value,
        )
        session.add(row)
        await session.commit()
    return {"status": "tracked"}


@app.get("/api/v1/analytics/events")
async def list_events(
    event_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    async with AsyncSessionLocal() as session:
        q = select(AnalyticsEvent).order_by(desc(AnalyticsEvent.created_at))
        if event_type:
            q = q.where(AnalyticsEvent.event_type == event_type)
        if entity_id:
            q = q.where(AnalyticsEvent.entity_id == entity_id)
        result = await session.execute(q.limit(limit))
        rows = result.scalars().all()

    return [
        {
            "id": r.id, "event_type": r.event_type, "entity_id": r.entity_id,
            "entity_type": r.entity_type, "client_id": r.client_id,
            "metadata": r.event_metadata, "value": r.value,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


# ── Dashboard Metrics ─────────────────────────────────────

@app.get("/api/v1/analytics/dashboard")
async def dashboard_metrics():
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)

        total_events = (await session.execute(
            select(func.count(AnalyticsEvent.id))
        )).scalar() or 0

        events_today = (await session.execute(
            select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.created_at >= day_ago)
        )).scalar() or 0

        by_type = (await session.execute(
            select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.created_at >= day_ago)
            .group_by(AnalyticsEvent.event_type)
        )).all()

    return {
        "total_events": total_events,
        "events_today": events_today,
        "by_type": {t: c for t, c in by_type},
    }


# ── Agent Performance ─────────────────────────────────────

@app.post("/api/v1/analytics/agents")
async def track_agent_metric(metric: AgentMetricCreate):
    async with AsyncSessionLocal() as session:
        row = AgentMetric(
            agent_name=metric.agent_name,
            pipeline_run_id=metric.pipeline_run_id,
            latency_ms=metric.latency_ms,
            success=1 if metric.success else 0,
            tokens_used=metric.tokens_used,
        )
        session.add(row)
        await session.commit()
    return {"status": "tracked"}


@app.get("/api/v1/analytics/agents")
async def agent_performance(hours: int = Query(24, ge=1, le=168)):
    async with AsyncSessionLocal() as session:
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await session.execute(
            select(
                AgentMetric.agent_name,
                func.count(AgentMetric.id).label("total_runs"),
                func.avg(AgentMetric.latency_ms).label("avg_latency_ms"),
                func.sum(AgentMetric.success).label("successes"),
                func.sum(AgentMetric.tokens_used).label("total_tokens"),
            )
            .where(AgentMetric.created_at >= since)
            .group_by(AgentMetric.agent_name)
        )
        rows = result.all()

    return [
        {
            "agent": r.agent_name,
            "total_runs": r.total_runs,
            "avg_latency_ms": round(r.avg_latency_ms or 0),
            "success_rate": round((r.successes or 0) / max(r.total_runs, 1) * 100, 1),
            "total_tokens": r.total_tokens or 0,
        }
        for r in rows
    ]


# ── Dashboard Endpoints (frontend /dashboard page) ───────

AGENT_NAMES = [
    ("Discovery Agent", "DSC"), ("Fact Extractor", "FCT"), ("Scriptwriter", "SCR"),
    ("Critic Agent", "CRT"), ("Headline Gen", "HDL"), ("Translator", "TRN"),
    ("SEO Agent", "SEO"), ("Avatar Producer", "AVT"), ("Publisher", "PUB"), ("Legal Agent", "LGL"),
]


@app.get("/api/v1/dashboard/agents")
async def dashboard_agents():
    async with AsyncSessionLocal() as session:
        stmt = (
            select(
                AgentMetricDashboard.agent_name,
                func.sum(AgentMetricDashboard.tasks_completed).label("tasks_completed"),
                func.avg(AgentMetricDashboard.latency_seconds).label("avg_latency"),
            )
            .group_by(AgentMetricDashboard.agent_name)
        )
        result = await session.execute(stmt)
        rows = result.all()

        latest_stmt = select(AgentMetricDashboard).order_by(AgentMetricDashboard.created_at.desc()).limit(50)
        latest_result = await session.execute(latest_stmt)
        latest = {r.agent_name: r for r in latest_result.scalars().all()}

    if not rows:
        return [
            {"name": n, "shortName": s, "tasks_completed": 0, "avg_latency": "--", "status": "idle", "last_run": "--"}
            for n, s in AGENT_NAMES
        ]
    return [
        {
            "name": r.agent_name,
            "tasks_completed": r.tasks_completed or 0,
            "avg_latency": f"{r.avg_latency:.1f}s" if r.avg_latency else "--",
            "status": latest[r.agent_name].status if r.agent_name in latest else "idle",
            "last_run": latest[r.agent_name].created_at.strftime("%H:%M:%S") if r.agent_name in latest else "--",
        }
        for r in rows
    ]


@app.get("/api/v1/dashboard/throughput")
async def dashboard_throughput():
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        day_ago = now - timedelta(hours=24)

        total_today = (await session.execute(
            select(func.count()).select_from(BroadcastScriptRow).where(BroadcastScriptRow.created_at >= day_ago)
        )).scalar() or 0

        hourly = []
        for i in range(23, -1, -1):
            hour_start = now - timedelta(hours=i + 1)
            hour_end = now - timedelta(hours=i)
            count = (await session.execute(
                select(func.count()).select_from(BroadcastScriptRow).where(
                    BroadcastScriptRow.created_at >= hour_start,
                    BroadcastScriptRow.created_at < hour_end,
                )
            )).scalar() or 0
            hourly.append({"hour": hour_end.strftime("%H:00"), "articles": count})

        cat_result = await session.execute(
            select(BroadcastScriptRow.category, func.count().label("count"))
            .where(BroadcastScriptRow.created_at >= day_ago)
            .group_by(BroadcastScriptRow.category)
            .order_by(func.count().desc())
            .limit(6)
        )
        categories = [{"category": r.category, "count": r.count} for r in cat_result.all()]

    return {
        "total_today": total_today,
        "avg_per_hour": round(total_today / 24, 1),
        "hourly": hourly,
        "categories": categories,
    }


@app.get("/api/v1/dashboard/revenue")
async def dashboard_revenue():
    async with AsyncSessionLocal() as session:
        total_clients = (await session.execute(
            select(func.count()).select_from(ClientAPIKey).where(ClientAPIKey.is_active == 1)
        )).scalar() or 0

        total_requests = (await session.execute(
            select(func.sum(ClientAPIKey.requests_used))
        )).scalar() or 0

        clients = (await session.execute(
            select(ClientAPIKey).where(ClientAPIKey.is_active == 1)
        )).scalars().all()

        tier_breakdown = {}
        for c in clients:
            tier_breakdown[c.plan_tier] = tier_breakdown.get(c.plan_tier, 0) + 1

    return {
        "total_clients": total_clients,
        "total_api_requests": total_requests or 0,
        "tier_breakdown": tier_breakdown,
        "clients": [
            {"name": c.client_name, "tier": c.plan_tier, "requests_used": c.requests_used, "monthly_quota": c.monthly_quota}
            for c in clients
        ],
    }


@app.get("/api/v1/dashboard/media-jobs")
async def dashboard_media_jobs(limit: int = Query(20, ge=1, le=50)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MediaJobRow).order_by(MediaJobRow.created_at.desc()).limit(limit)
        )
        return [
            {
                "id": r.id, "script_id": r.script_id, "headline": r.headline,
                "media_type": r.media_type, "language": r.language,
                "status": r.status, "progress": r.progress,
                "duration": r.duration, "output_url": r.output_url,
                "created_at": r.created_at.isoformat(),
            }
            for r in result.scalars().all()
        ]


@app.get("/api/v1/dashboard/system")
async def dashboard_system():
    try:
        import psutil
        process = psutil.Process()
        mem = process.memory_info()
        cpu = psutil.cpu_percent(interval=0.1)
        mem_mb = round(mem.rss / 1024 / 1024, 1)
        mem_pct = round(process.memory_percent(), 1)
        disk_pct = psutil.disk_usage("/").percent
    except Exception:
        cpu, mem_mb, mem_pct, disk_pct = 0, 0, 0, 0

    return {
        "cpu_percent": cpu,
        "memory_used_mb": mem_mb,
        "memory_percent": mem_pct,
        "disk_usage_percent": disk_pct,
        "redis_status": "connected" if os.getenv("REDIS_URL") else "not_configured",
        "celery_status": "connected" if os.getenv("REDIS_URL") else "not_configured",
        "scripts_in_memory": 0,
        "social_platforms": [],
        "social_auto_post": False,
    }


# ── Scripts endpoint (so dashboard can fetch scripts directly) ──

class ScriptSync(BaseModel):
    id: str
    headline: str
    english_script: str
    hindi_script: str = ""
    category: str = "general"
    source_url: str = ""
    word_count_en: int = 0
    word_count_hi: int = 0
    estimated_duration_seconds: int = 0


@app.post("/api/v1/scripts/sync")
async def sync_script(data: ScriptSync):
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(BroadcastScriptRow).where(BroadcastScriptRow.id == data.id)
        )).scalars().first()
        if not existing:
            row = BroadcastScriptRow(
                id=data.id, headline=data.headline,
                english_script=data.english_script, hindi_script=data.hindi_script,
                category=data.category, source_url=data.source_url,
                word_count_en=data.word_count_en, word_count_hi=data.word_count_hi,
                estimated_duration_seconds=data.estimated_duration_seconds,
            )
            session.add(row)
            await session.commit()
    return {"status": "synced"}


@app.get("/api/v1/scripts")
async def list_scripts(limit: int = Query(20, ge=1, le=100)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BroadcastScriptRow).order_by(desc(BroadcastScriptRow.created_at)).limit(limit)
        )
        rows = result.scalars().all()
    return [
        {
            "id": r.id, "headline": r.headline, "english_script": r.english_script,
            "hindi_script": r.hindi_script, "category": r.category,
            "source_url": r.source_url, "word_count_en": r.word_count_en,
            "word_count_hi": r.word_count_hi, "estimated_duration_seconds": r.estimated_duration_seconds,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
