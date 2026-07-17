"""
A.N.N. Notification Service
Social media posting, webhook delivery, and real-time WebSocket broadcasting.
"""

import time
import asyncio
from contextlib import asynccontextmanager

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_settings
import social
import webhooks
from websocket_manager import manager, redis_listener

settings = get_settings()
START_TIME = time.time()


class BroadcastRequest(BaseModel):
    headline: str
    excerpt: str = ""
    category: str = "general"
    script_id: str = ""


class WebhookRequest(BaseModel):
    clients: list[dict]
    payload: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(redis_listener())
    yield


app = FastAPI(
    title="A.N.N. Notification Service",
    description="Social media posting, webhook delivery, and WebSocket broadcasting.",
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
    return {
        "service": "notification-service",
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "enabled_platforms": social.get_enabled_platforms(),
    }


@app.post("/api/v1/social/broadcast")
async def broadcast_to_social(req: BroadcastRequest):
    result = await social.broadcast_all(req.headline, req.excerpt, req.category, req.script_id)
    return result


@app.get("/api/v1/social/status")
async def social_status():
    return {"enabled_platforms": social.get_enabled_platforms()}


@app.post("/api/v1/webhooks/dispatch")
async def dispatch(req: WebhookRequest):
    await webhooks.dispatch_webhooks(req.clients, req.payload)
    return {"status": "dispatched", "client_count": len(req.clients)}


@app.websocket("/ws/breaking-news")
async def breaking_news_ws(websocket: WebSocket, api_key: str = Query(None)):
    if not api_key:
        await websocket.close(code=1008, reason="Missing API key")
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
