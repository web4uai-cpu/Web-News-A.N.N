"""
A.N.N. Realtime Layer
WebSocket connection management + Redis pub/sub bridge from Celery workers.
"""

import json
import os

from fastapi import WebSocket

from utils.logger import get_logger

log = get_logger("realtime")

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info("websocket_client_connected", count=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        log.info("websocket_client_disconnected", count=len(self.active_connections))

    async def broadcast_news(self, script_data: dict):
        """Streams breaking news updates instantaneously to all active clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(script_data)
            except Exception:
                pass

    async def broadcast_direct_to_client(self, api_key: str, payload: dict):
        """Streams a custom isolated generation back to the specific client."""
        # Note: In production, track mapping of api_keys -> websockets better
        for connection in self.active_connections:
            query_params = connection.query_params
            if query_params.get("api_key") == api_key:
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass


ws_manager = ConnectionManager()


async def listen_to_redis_broadcasts():
    """
    Runs permanently in the background of FastAPI.
    Listens to the 'ann_broadcasts' channel on Redis. When a Celery node finishes
    generating an AI video, it publishes the MP4 URL here. This listener grabs it
    and fires it instantaneously up the WebSockets to the client's browser.
    """
    log.info("redis_pubsub_listener_started")
    try:
        import redis.asyncio as aioredis
        redis = aioredis.from_url(redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe("ann_broadcasts")

        async for message in pubsub.listen():
            if message["type"] == "message":
                payload = json.loads(message["data"])
                api_key = payload.get("api_key")
                if api_key:
                    log.info("symphony_routing_delivery_to_client", topic=payload.get("topic"))
                    await ws_manager.broadcast_direct_to_client(api_key, payload)
    except Exception as e:
        log.error("redis_pubsub_listener_failed", error=str(e))
