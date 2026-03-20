"""
A.N.N. API Gateway and B2B Auth
Manages enterprise client access and API key verification.
"""

"""
A.N.N. API Gateway and B2B Auth
Manages enterprise client access, API key verification, and auto-billing limits.
"""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.future import select
from models.b2b_database import AsyncSessionLocal, ClientAPIKey

api_key_header = APIKeyHeader(name="X-ANN-API-Key", auto_error=False)

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
        result = await session.execute(
            select(ClientAPIKey).where(ClientAPIKey.api_key == api_key_header)
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
            "webhook_url": client.webhook_url
        }
