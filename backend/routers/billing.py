"""Stripe B2B revenue endpoints: checkout + provisioning webhook."""

from fastapi import APIRouter, Query, Request

from config import get_settings
from services.billing import create_checkout_session, handle_stripe_webhook

router = APIRouter()
settings = get_settings()


@router.post("/api/v1/b2b/checkout", tags=["Revenue Engine"])
async def b2b_checkout(
    tier: str = Query("pro", description="standard, pro, enterprise"),
    client_name: str = Query(..., description="Your Company Name"),
    currency: str = Query("usd", description="usd or inr"),
):
    """Redirects the client to Stripe to purchase an API key subscription."""
    url_payload = await create_checkout_session(
        tier, client_name,
        success_url=f"{settings.public_url}/portal?payment=success",
        cancel_url=f"{settings.public_url}/portal?payment=cancelled",
        currency=currency,
    )
    return url_payload


@router.post("/api/v1/webhooks/stripe", tags=["Revenue Engine"])
async def stripe_webhook(request: Request):
    """Stripe webhook to auto-provision B2B API keys upon successful payment."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    return await handle_stripe_webhook(payload, sig_header)
