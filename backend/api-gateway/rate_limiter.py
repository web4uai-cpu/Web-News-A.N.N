"""
Redis-backed sliding window rate limiter for inbound API requests.
"""

import time
import redis.asyncio as aioredis
from config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    global _redis
    if _redis is None:
        settings = get_settings()
        try:
            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
        except Exception:
            _redis = None
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> tuple[bool, int]:
    """
    Sliding window rate limit check.

    Returns:
        (allowed: bool, remaining: int)
    """
    r = await get_redis()
    if r is None:
        return True, max_requests

    now = time.time()
    window_start = now - window_seconds
    pipe_key = f"rl:{key}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(pipe_key, 0, window_start)
    pipe.zadd(pipe_key, {str(now): now})
    pipe.zcard(pipe_key)
    pipe.expire(pipe_key, window_seconds + 1)
    results = await pipe.execute()

    current_count = results[2]
    allowed = current_count <= max_requests
    remaining = max(0, max_requests - current_count)

    if not allowed:
        await r.zrem(pipe_key, str(now))

    return allowed, remaining
