"""
A.N.N. Webhook Dispatcher
Automatically pushes generated news broadcasts to B2B enterprise clients.
"""

import httpx
import asyncio
from sqlalchemy.future import select
from models.b2b_database import AsyncSessionLocal, ClientAPIKey
from models.schemas import PipelineJob
from utils.logger import get_logger

log = get_logger("webhook_dispatcher")

async def dispatch_webhooks(job: PipelineJob):
    """
    Finds all active enterprise clients with a configured webhook URL
    and pushes the completed pipeline job (Scripts + Videos) to them.
    """
    if not job.scripts and not job.video_results:
        log.warning("webhook_skip_empty_job", job_id=job.job_id)
        return

    async with AsyncSessionLocal() as session:
        # Get all active clients who have a webhook URL configured
        result = await session.execute(
            select(ClientAPIKey)
            .where(ClientAPIKey.is_active == True)
            .where(ClientAPIKey.webhook_url != None)
            .where(ClientAPIKey.webhook_url != "")
        )
        clients = result.scalars().all()

    if not clients:
        log.info("webhook_no_clients", job_id=job.job_id)
        return

    # Prepare Payload
    payload = {
        "event": "broadcast.ready",
        "job_id": job.job_id,
        "scripts": [
            {
                "headline": s.headline,
                "english_script": s.english_script,
                "translations": s.translations,
                "category": s.category.value
            } for s in job.scripts
        ],
        "videos": [
            {
                "language": v.language.value,
                "video_url": v.video_url,
                "heygen_video_id": v.heygen_video_id
            } for v in job.video_results if v.video_url
        ]
    }

    log.info("webhook_dispatching", job_id=job.job_id, client_count=len(clients))

    # Dispatch concurrently to all clients
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for b2b_client in clients:
            tasks.append(
                _send_webhook(
                    client=client, 
                    url=b2b_client.webhook_url, 
                    payload=payload, 
                    client_name=b2b_client.client_name
                )
            )
        
        await asyncio.gather(*tasks, return_exceptions=True)

async def _send_webhook(client: httpx.AsyncClient, url: str, payload: dict, client_name: str):
    """Sends the actual HTTP POST request to the client."""
    try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        log.info("webhook_success", client=client_name, url=url, status=response.status_code)
    except Exception as e:
        log.error("webhook_failed", client=client_name, url=url, error=str(e))
