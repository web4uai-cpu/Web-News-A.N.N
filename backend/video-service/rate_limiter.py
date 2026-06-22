"""
Token-bucket rate limiter for external API calls (ElevenLabs, HeyGen).
"""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    rate: float
    capacity: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.rate)
                self.last_refill = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
                self._lock.release()
                await asyncio.sleep(wait)
                await self._lock.acquire()


_buckets: dict[str, TokenBucket] = {}


def register(name: str, rpm: int):
    _buckets[name] = TokenBucket(rate=rpm / 60.0, capacity=1.0)


async def acquire(name: str):
    bucket = _buckets.get(name)
    if bucket:
        await bucket.acquire()
