"""
A.N.N. Analytics Service
Event tracking, engagement metrics, agent performance scoring, and dashboard data.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy import func, desc

from config import get_settings
from database import init_db, AsyncSessionLocal, AnalyticsEvent, AgentMetric

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
            metadata=event.metadata,
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
            "metadata": r.metadata, "value": r.value,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
