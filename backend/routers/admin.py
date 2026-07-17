"""Admin control panel: B2B client provisioning and runtime settings. Admin-gated."""

import os
import uuid
from typing import Dict

from dotenv import set_key
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.future import select

from core.security import hash_api_key, key_prefix, require_admin
from models.b2b_database import AsyncSessionLocal, ClientAPIKey
from utils.logger import get_logger

router = APIRouter()
log = get_logger("admin_router")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class B2BClientCreate(BaseModel):
    client_name: str
    plan_tier: str = "standard"
    monthly_quota: int = 1000
    webhook_url: str | None = None


@router.post("/api/v1/admin/clients", tags=["Admin Control Panel (B2B SaaS)"])
async def create_b2b_client(
    client: B2BClientCreate,
    _admin: bool = Depends(require_admin),
):
    """
    Generate a new API Key for a B2B partner.
    The raw key is returned once and stored only as a SHA-256 hash.
    """
    new_api_key = f"ann_{client.plan_tier}_{uuid.uuid4().hex[:12]}"

    async with AsyncSessionLocal() as session:
        new_client = ClientAPIKey(
            client_name=client.client_name,
            api_key=hash_api_key(new_api_key),
            key_prefix=key_prefix(new_api_key),
            plan_tier=client.plan_tier,
            monthly_quota=client.monthly_quota,
            webhook_url=client.webhook_url,
        )
        session.add(new_client)
        await session.commit()

    log.info("admin_created_b2b_client", client_name=client.client_name, key_prefix=key_prefix(new_api_key))

    return {
        "message": "B2B Client Created Successfully. Store this key now — it cannot be retrieved again.",
        "client_name": client.client_name,
        "api_key": new_api_key,
        "monthly_quota": client.monthly_quota,
        "webhook_url": client.webhook_url,
    }


@router.get("/api/v1/admin/clients", tags=["Admin Control Panel (B2B SaaS)"])
async def list_b2b_clients(
    _admin: bool = Depends(require_admin),
):
    """List all deployed API keys (masked) and quota usage."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ClientAPIKey))
        clients = result.scalars().all()

    return [
        {
            "id": c.id,
            "client_name": c.client_name,
            "api_key": c.key_prefix or "(hashed)",
            "plan_tier": c.plan_tier,
            "quota": f"{c.requests_used}/{c.monthly_quota}",
            "webhook_url": c.webhook_url,
            "active": c.is_active,
        } for c in clients
    ]


@router.get("/api/v1/admin/settings", tags=["Admin Control Panel (Settings)"])
async def get_system_settings(_admin: bool = Depends(require_admin)):
    """Retrieve current system API keys safely masked. Admin only."""

    def _mask(val: str | None) -> str:
        if not val or len(val) < 8: return ""
        return f"{val[:4]}...{val[-4:]}"

    return {
        "LLM_API_KEY": _mask(os.getenv("LLM_API_KEY")),
        "NEWS_API_KEY": _mask(os.getenv("NEWS_API_KEY")),
        "ALPHA_VANTAGE_KEY": _mask(os.getenv("ALPHA_VANTAGE_KEY")),
        "ELEVENLABS_API_KEY": _mask(os.getenv("ELEVENLABS_API_KEY")),
        "HEYGEN_API_KEY": _mask(os.getenv("HEYGEN_API_KEY")),
        "TWITTER_BEARER_TOKEN": _mask(os.getenv("TWITTER_BEARER_TOKEN")),
        "FACEBOOK_PAGE_TOKEN": _mask(os.getenv("FACEBOOK_PAGE_TOKEN")),
        "INSTAGRAM_ACCESS_TOKEN": _mask(os.getenv("INSTAGRAM_ACCESS_TOKEN")),
        "INSTAGRAM_ACCOUNT_ID": _mask(os.getenv("INSTAGRAM_ACCOUNT_ID")),
    }


@router.post("/api/v1/admin/settings", tags=["Admin Control Panel (Settings)"])
async def update_system_settings(settings_payload: Dict[str, str], _admin: bool = Depends(require_admin)):
    """Update API keys dynamically by rewriting the .env file. Admin only."""
    env_path = os.path.join(BACKEND_DIR, ".env")

    # Ensure .env exists
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("# A.N.N. Environment Configuration\n")

    accepted_keys = [
        "LLM_API_KEY", "NEWS_API_KEY", "ALPHA_VANTAGE_KEY",
        "ELEVENLABS_API_KEY", "HEYGEN_API_KEY",
        "TWITTER_BEARER_TOKEN", "FACEBOOK_PAGE_TOKEN",
        "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"
    ]

    updated_count = 0
    for key, val in settings_payload.items():
        if key in accepted_keys and val:
            # Overwrite the actual .env file programmatically
            set_key(env_path, key, val)
            # Update memory immediately without rebooting
            os.environ[key] = val
            updated_count += 1

    log.info("admin_updated_settings", updated_keys=updated_count)
    return {"message": f"Successfully safely updated {updated_count} API Keys.", "status": "success"}
