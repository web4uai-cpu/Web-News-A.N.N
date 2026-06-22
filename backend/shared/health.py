"""
Standardized health check for all A.N.N. microservices.
"""

import time
import asyncio
from typing import Callable, Awaitable

import httpx
import redis.asyncio as aioredis


class HealthChecker:
    def __init__(self, service_name: str, start_time: float):
        self.service_name = service_name
        self.start_time = start_time
        self._checks: list[tuple[str, Callable[[], Awaitable[bool]]]] = []

    def add_check(self, name: str, check_fn: Callable[[], Awaitable[bool]]):
        self._checks.append((name, check_fn))

    async def check(self) -> dict:
        results = {}
        all_healthy = True

        for name, fn in self._checks:
            try:
                healthy = await asyncio.wait_for(fn(), timeout=5.0)
                results[name] = "healthy" if healthy else "unhealthy"
                if not healthy:
                    all_healthy = False
            except Exception as e:
                results[name] = f"error: {str(e)[:100]}"
                all_healthy = False

        return {
            "service": self.service_name,
            "status": "healthy" if all_healthy else "degraded",
            "uptime_seconds": round(time.time() - self.start_time, 1),
            "checks": results,
        }


async def check_redis(redis_url: str) -> bool:
    try:
        r = aioredis.from_url(redis_url)
        await r.ping()
        await r.aclose()
        return True
    except Exception:
        return False


async def check_service(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{url}/health")
            return r.status_code == 200
    except Exception:
        return False


async def check_database(session_factory) -> bool:
    try:
        async with session_factory() as session:
            await session.execute("SELECT 1" if hasattr(session, "execute") else None)
        return True
    except Exception:
        return False
