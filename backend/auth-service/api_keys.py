"""
B2B API key management — create, list, verify, and revoke API keys.
"""

import uuid
from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.future import select
from pydantic import BaseModel

from database import AsyncSessionLocal, ClientAPIKey
from config import get_settings

router = APIRouter(tags=["API Keys"])
api_key_header = APIKeyHeader(name="X-ANN-API-Key", auto_error=False)


class ClientCreate(BaseModel):
    client_name: str
    plan_tier: str = "standard"
    monthly_quota: int = 1000
    webhook_url: str | None = None


async def verify_api_key(api_key: str = Security(api_key_header)) -> dict:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="B2B API Key is missing. Pass X-ANN-API-Key header.",
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ClientAPIKey).where(ClientAPIKey.api_key == api_key)
        )
        client = result.scalars().first()

        if not client or not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or disabled B2B API Key.",
            )

        if client.requests_used >= client.monthly_quota:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Monthly quota of {client.monthly_quota} requests exceeded.",
            )

        client.requests_used += 1
        await session.commit()

        return {
            "name": client.client_name,
            "plan": client.plan_tier,
            "requests_used": client.requests_used,
            "monthly_quota": client.monthly_quota,
            "webhook_url": client.webhook_url,
        }


@router.post("/api/v1/admin/clients")
async def create_client(client: ClientCreate):
    new_key = f"ann_{client.plan_tier}_{uuid.uuid4().hex[:12]}"

    async with AsyncSessionLocal() as session:
        new_client = ClientAPIKey(
            client_name=client.client_name,
            api_key=new_key,
            plan_tier=client.plan_tier,
            monthly_quota=client.monthly_quota,
            webhook_url=client.webhook_url,
        )
        session.add(new_client)
        await session.commit()

    return {
        "message": "B2B Client Created Successfully",
        "client_name": client.client_name,
        "api_key": new_key,
        "monthly_quota": client.monthly_quota,
        "webhook_url": client.webhook_url,
    }


@router.get("/api/v1/admin/clients")
async def list_clients():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ClientAPIKey))
        clients = result.scalars().all()

    return [
        {
            "id": c.id,
            "client_name": c.client_name,
            "api_key": c.api_key,
            "plan_tier": c.plan_tier,
            "quota": f"{c.requests_used}/{c.monthly_quota}",
            "webhook_url": c.webhook_url,
            "active": c.is_active,
        }
        for c in clients
    ]


@router.get("/api/v1/b2b/portal/metrics")
async def portal_metrics(client: dict = Security(verify_api_key)):
    return {
        "client_name": client["name"],
        "plan_tier": client["plan"],
        "requests_used": client["requests_used"],
        "monthly_quota": client["monthly_quota"],
    }
