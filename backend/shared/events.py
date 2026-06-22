"""
A.N.N. Event Bus — Redis Streams for async inter-service communication.

Events flow between microservices without direct HTTP coupling:
  article-service  →  article.created   →  search-service (index)
  article-service  →  article.created   →  notification-service (social post)
  video-service    →  video.completed   →  notification-service (WebSocket push)
  pipeline         →  pipeline.completed →  analytics-service (track)

Usage:
    from shared.events import EventBus

    bus = EventBus("redis://localhost:6379/0")

    # Publish
    await bus.publish("article.created", {"id": "abc", "headline": "..."})

    # Subscribe (in service startup)
    async for event in bus.subscribe("article.created"):
        await handle_article(event)
"""

import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator

import redis.asyncio as aioredis


class EventBus:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def close(self):
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def publish(self, event_type: str, payload: dict) -> str:
        """
        Publish an event to a Redis Stream.

        Args:
            event_type: Stream name (e.g., "article.created")
            payload: Event data dict

        Returns:
            Stream entry ID
        """
        r = await self._get_redis()
        data = {
            "type": event_type,
            "payload": json.dumps(payload),
            "timestamp": datetime.utcnow().isoformat(),
        }
        entry_id = await r.xadd(f"ann:events:{event_type}", data, maxlen=10000)
        return entry_id

    async def subscribe(
        self,
        event_type: str,
        group: str = "default",
        consumer: str = "worker-1",
        batch_size: int = 10,
        block_ms: int = 5000,
    ) -> AsyncGenerator[dict, None]:
        """
        Subscribe to a Redis Stream as a consumer group.
        Yields events as they arrive.

        Args:
            event_type: Stream name to subscribe to
            group: Consumer group name (for load balancing across instances)
            consumer: Consumer name within the group
            batch_size: Max events per read
            block_ms: Block timeout in ms (0 = forever)
        """
        r = await self._get_redis()
        stream = f"ann:events:{event_type}"

        # Create consumer group if it doesn't exist
        try:
            await r.xgroup_create(stream, group, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        while True:
            try:
                entries = await r.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={stream: ">"},
                    count=batch_size,
                    block=block_ms,
                )

                if not entries:
                    continue

                for stream_name, messages in entries:
                    for msg_id, data in messages:
                        try:
                            event = {
                                "id": msg_id,
                                "type": data.get("type", event_type),
                                "payload": json.loads(data.get("payload", "{}")),
                                "timestamp": data.get("timestamp", ""),
                            }
                            yield event

                            # Acknowledge processed event
                            await r.xack(stream, group, msg_id)
                        except json.JSONDecodeError:
                            await r.xack(stream, group, msg_id)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    async def publish_and_forget(self, event_type: str, payload: dict):
        """Fire-and-forget publish — swallows errors."""
        try:
            await self.publish(event_type, payload)
        except Exception:
            pass


# Pre-defined event types
class Events:
    ARTICLE_CREATED = "article.created"
    ARTICLE_UPDATED = "article.updated"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    VIDEO_REQUESTED = "video.requested"
    VIDEO_COMPLETED = "video.completed"
    AUDIO_COMPLETED = "audio.completed"
    SOCIAL_POSTED = "social.posted"
    WEBHOOK_DISPATCHED = "webhook.dispatched"
    CLIENT_CREATED = "client.created"
    SEARCH_INDEXED = "search.indexed"
