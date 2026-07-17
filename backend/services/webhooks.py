"""
A.N.N. Outbound Webhooks
HMAC-SHA256-signed event delivery to B2B clients.

Signature scheme (documented for consumers):
  X-ANN-Event:      event name, e.g. "script.created"
  X-ANN-Timestamp:  unix seconds when the request was signed
  X-ANN-Signature:  "sha256=" + HMAC_SHA256(secret, f"{timestamp}.{raw_body}")

Consumers must recompute the HMAC over `timestamp + "." + body` and use a
constant-time comparison; reject requests older than ~5 minutes to prevent replay.
"""

import asyncio
import hashlib
import hmac
import json
import time

import httpx
from sqlalchemy import select

from utils.logger import get_logger

log = get_logger("webhooks")

DELIVERY_TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 3


def sign_payload(secret: str, timestamp: int, body: bytes) -> str:
    mac = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


async def deliver_webhook(url: str, secret: str | None, event: str, payload: dict) -> bool:
    """POST a signed event to one endpoint, with basic retry/backoff."""
    body = json.dumps({"event": event, "data": payload}, default=str).encode("utf-8")
    timestamp = int(time.time())
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ANN-Webhooks/1.0",
        "X-ANN-Event": event,
        "X-ANN-Timestamp": str(timestamp),
    }
    if secret:
        headers["X-ANN-Signature"] = sign_payload(secret, timestamp, body)

    async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT_SECONDS) as client:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = await client.post(url, content=body, headers=headers)
                if resp.status_code < 300:
                    log.info("webhook_delivered", url=url, event=event, status=resp.status_code)
                    return True
                log.warning("webhook_rejected", url=url, event=event, status=resp.status_code, attempt=attempt)
            except Exception as e:
                log.warning("webhook_delivery_error", url=url, event=event, attempt=attempt, error=str(e))
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(2 ** attempt)
    log.error("webhook_delivery_failed", url=url, event=event, attempts=MAX_ATTEMPTS)
    return False


async def broadcast_event(event: str, payload: dict) -> None:
    """
    Fire an event to every active client with a webhook_url configured.
    Failures are logged, never raised — callers fire-and-forget.
    """
    from models.b2b_database import AsyncSessionLocal, ClientAPIKey

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ClientAPIKey).where(
                    ClientAPIKey.is_active == True,  # noqa: E712
                    ClientAPIKey.webhook_url.isnot(None),
                    ClientAPIKey.webhook_url != "",
                )
            )
            targets = [(c.webhook_url, c.webhook_secret) for c in result.scalars().all()]
    except Exception as e:
        log.error("webhook_targets_query_failed", error=str(e))
        return

    if not targets:
        return

    await asyncio.gather(
        *(deliver_webhook(url, secret, event, payload) for url, secret in targets),
        return_exceptions=True,
    )
