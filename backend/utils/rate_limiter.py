"""
A.N.N. Rate Limiter
Token-bucket rate limiter for external API calls.
Prevents hitting API quotas and ensures graceful degradation.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from utils.logger import get_logger

log = get_logger("rate_limiter")


@dataclass
class TokenBucket:
    """Token bucket implementation for rate limiting."""

    rate: float  # tokens per second
    capacity: float  # max burst capacity
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until the requested number of tokens are available."""
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Calculate wait time for next token
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate
                log.debug(
                    "rate_limit_wait",
                    wait_seconds=round(wait_time, 2),
                    tokens_needed=tokens,
                    tokens_available=round(self.tokens, 2),
                )
                # Release lock while waiting
                self._lock.release()
                await asyncio.sleep(wait_time)
                await self._lock.acquire()

    def _refill(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now


class RateLimiterRegistry:
    """
    Manages multiple named rate limiters.
    Usage:
        limiter = RateLimiterRegistry()
        limiter.register("openai", rpm=60)
        await limiter.acquire("openai")
    """

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    def register(self, name: str, rpm: int, burst: float = 1.0) -> None:
        """Register a new rate limiter with requests-per-minute limit."""
        rate = rpm / 60.0  # Convert RPM to tokens per second
        self._buckets[name] = TokenBucket(rate=rate, capacity=float(burst))
        log.info("rate_limiter_registered", name=name, rpm=rpm, burst=burst)

    async def acquire(self, name: str) -> None:
        """Acquire a token from the named rate limiter."""
        bucket = self._buckets.get(name)
        if bucket is None:
            log.warning("rate_limiter_not_found", name=name)
            return
        await bucket.acquire()

    def is_registered(self, name: str) -> bool:
        return name in self._buckets


# ── Global singleton ────────────────────────────────────
rate_limiter = RateLimiterRegistry()
