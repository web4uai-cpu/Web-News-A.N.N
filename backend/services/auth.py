"""
A.N.N. B2B Auth
Manages enterprise client access, API key verification, and auto-billing limits.
Keys are stored as SHA-256 hashes; legacy plaintext rows are still matched
so existing clients keep working until rotated.
"""

import time
from collections import defaultdict, deque

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.future import select

from core.security import hash_api_key
from models.b2b_database import AsyncSessionLocal, ClientAPIKey

api_key_header = APIKeyHeader(name="X-ANN-API-Key", auto_error=False)

# ── Per-key rate limiting (sliding 60s window, by plan tier) ──
TIER_RPM = {"free": 30, "standard": 60, "pro": 300, "enterprise": 1200}
_request_windows: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(key_id: str, plan_tier: str) -> None:
    """Raise 429 when the key exceeds its tier's requests-per-minute budget."""
    limit = TIER_RPM.get(plan_tier, TIER_RPM["standard"])
    now = time.monotonic()
    window = _request_windows[key_id]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit} requests/minute for tier '{plan_tier}'. Retry shortly.",
            headers={"Retry-After": "60"},
        )
    window.append(now)


async def get_client_by_key(raw_key: str, session=None) -> ClientAPIKey | None:
    """Look up a client by raw API key — hashed first, plaintext legacy fallback."""
    async def _lookup(sess):
        for candidate in (hash_api_key(raw_key), raw_key):
            result = await sess.execute(
                select(ClientAPIKey).where(ClientAPIKey.api_key == candidate)
            )
            client = result.scalars().first()
            if client:
                return client
        return None

    if session is not None:
        return await _lookup(session)
    async with AsyncSessionLocal() as sess:
        return await _lookup(sess)


async def verify_b2b_api_key(api_key_header: str = Security(api_key_header)):
    """
    Dependency to check if the caller provided a valid B2B API Key from the Database.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="B2B API Key is missing. Pass X-ANN-API-Key header.",
        )

    async with AsyncSessionLocal() as session:
        client = await get_client_by_key(api_key_header, session)

        if not client or not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or disabled B2B API Key.",
            )

        check_rate_limit(str(client.id), client.plan_tier)

        if client.requests_used >= client.monthly_quota:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Monthly quota of {client.monthly_quota} requests exceeded. Please renew your limits.",
            )

        # Deduct quota block
        client.requests_used += 1
        await session.commit()

        # Return simplified dict matching expected caller format
        return {
            "name": client.client_name,
            "plan": client.plan_tier,
            "requests_used": client.requests_used,
            "webhook_url": client.webhook_url,
        }
