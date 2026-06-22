"""
Webhook dispatcher — pushes new content to B2B client endpoints.
"""

import httpx
import asyncio


async def dispatch_webhooks(clients: list[dict], payload: dict):
    """
    Send webhook POST to all clients with a configured webhook_url.

    Args:
        clients: List of dicts with 'client_name' and 'webhook_url' keys.
        payload: JSON payload to deliver.
    """
    if not clients:
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [
            _send(client, c["webhook_url"], payload, c["client_name"])
            for c in clients
            if c.get("webhook_url")
        ]
        await asyncio.gather(*tasks, return_exceptions=True)


async def _send(client: httpx.AsyncClient, url: str, payload: dict, name: str) -> dict:
    try:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return {"client": name, "status": "delivered", "code": r.status_code}
    except Exception as e:
        return {"client": name, "status": "failed", "error": str(e)}
