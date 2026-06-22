"""
WebSocket connection manager for real-time breaking news push.
"""

import json
import asyncio
import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect
from config import get_settings


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        for ws in list(self.connections):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(ws)

    async def send_to_key(self, api_key: str, data: dict):
        for ws in list(self.connections):
            try:
                if ws.query_params.get("api_key") == api_key:
                    await ws.send_json(data)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()


async def redis_listener():
    """Listen for Redis Pub/Sub broadcasts from Celery workers and relay to WebSocket clients."""
    settings = get_settings()
    try:
        r = aioredis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe("ann_broadcasts")

        async for message in pubsub.listen():
            if message["type"] == "message":
                payload = json.loads(message["data"])
                api_key = payload.get("api_key")
                if api_key:
                    await manager.send_to_key(api_key, payload)
                else:
                    await manager.broadcast(payload)
    except Exception:
        pass
