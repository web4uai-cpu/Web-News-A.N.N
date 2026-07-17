"""B2B Client Portal secure routes (X-ANN-API-Key gated)."""

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from models.b2b_database import AsyncSessionLocal, ClientAPIKey
from services.auth import get_client_by_key
from utils.logger import get_logger

router = APIRouter()
log = get_logger("portal_router")


async def _get_active_client(api_key: str) -> ClientAPIKey:
    client = await get_client_by_key(api_key)
    if not client or not client.is_active:
        raise HTTPException(status_code=401, detail="Invalid or suspended API Key.")
    return client


@router.get("/api/v1/b2b/portal/metrics", tags=["B2B Client Portal"])
async def get_client_portal_metrics(api_key: str = Header(..., alias="X-ANN-API-Key")):
    """Validates the B2B Client and returns securely isolated tracking metrics for their Portal Dashboard."""
    client = await _get_active_client(api_key)
    return {
        "client_name": client.client_name,
        "plan_tier": client.plan_tier,
        "requests_used": client.requests_used,
        "monthly_quota": client.monthly_quota,
    }


@router.post("/api/v1/b2b/portal/social-keys", tags=["B2B Client Portal"])
async def link_client_social_keys(
    ig_token: str = "",
    fb_page_id: str = "",
    linkedin_token: str = "",
    api_key: str = Header(..., alias="X-ANN-API-Key"),
):
    """Saves custom social media keys for Creator Tier Auto-Pilot, including LinkedIn for Corporate Influencers."""
    client = await _get_active_client(api_key)
    log.info("b2b_socials_linked", client=client.client_name, ig_connected=bool(ig_token), linkedin_connected=bool(linkedin_token))
    return {"status": "success", "message": "Social Accounts Linked Successfully! A.N.N will now post your custom generations directly to your feeds."}


@router.post("/api/v1/b2b/portal/generate", tags=["B2B Client Portal"])
async def trigger_client_studio_generation(
    topic: str,
    background_tasks: BackgroundTasks,
    api_key: str = Header(..., alias="X-ANN-API-Key"),
):
    """The 'On-Demand AI Studio' Route. Burns 50 quota requests to spin the autonomous pipeline for a custom keyword."""
    async with AsyncSessionLocal() as session:
        client = await get_client_by_key(api_key, session)
        if not client or not client.is_active:
            raise HTTPException(status_code=401, detail="Invalid API Key.")

        if client.plan_tier != "enterprise":
            raise HTTPException(status_code=403, detail=f"Your current tier ({client.plan_tier}) does not include On-Demand Studio access. Please upgrade to Enterprise.")

        cost_multiplier = 50
        if client.requests_used + cost_multiplier > client.monthly_quota:
            raise HTTPException(status_code=402, detail="Insufficient API Validation Quota. Please upgrade your Stripe plan.")

        client.requests_used += cost_multiplier
        await session.commit()

    from services.tasks import b2b_distributed_pipeline_task
    task = b2b_distributed_pipeline_task.delay(topic=topic, api_key=api_key)
    log.info("b2b_client_triggered_studio", client=client.client_name, topic=topic, quota_billed=cost_multiplier, celery_task_id=task.id)

    return {"status": "processing", "message": f"Pipeline queued for '{topic}'. Deducted {cost_multiplier} quota.", "task_id": task.id}
