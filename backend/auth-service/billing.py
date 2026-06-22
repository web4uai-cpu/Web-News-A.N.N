"""
Stripe billing — checkout sessions and webhook handling.
"""

import uuid
import stripe
from fastapi import APIRouter, Request, HTTPException

from database import AsyncSessionLocal, ClientAPIKey
from config import get_settings

router = APIRouter(tags=["Billing"])
settings = get_settings()
stripe.api_key = settings.stripe_secret_key

TIER_LIMITS = {
    "standard": 5000,
    "pro": 25000,
    "enterprise": 100000,
}


@router.post("/api/v1/b2b/checkout")
async def checkout(tier: str = "pro", client_name: str = "Client", currency: str = "usd"):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API keys are not configured.")
    if tier not in TIER_LIMITS:
        raise HTTPException(status_code=400, detail="Invalid plan tier.")

    prices = {
        "usd": {"standard": 4900, "pro": 19900, "enterprise": 99900},
        "inr": {"standard": 399900, "pro": 1599900, "enterprise": 7999900},
    }
    cur = currency.lower() if currency.lower() in prices else "usd"
    amount = prices[cur].get(tier, prices[cur]["standard"])

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": cur,
                    "product_data": {
                        "name": f"A.N.N. API - {tier.upper()} Tier",
                        "description": f"Up to {TIER_LIMITS[tier]} API requests per month.",
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{settings.supabase_url or 'http://localhost:3000'}/portal?payment=success",
            cancel_url=f"{settings.supabase_url or 'http://localhost:3000'}/portal?payment=cancelled",
            client_reference_id=client_name,
            metadata={"tier": tier, "client_name": client_name},
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create payment session.")


@router.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    if not settings.stripe_webhook_secret:
        return {"status": "ignored"}

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        client_name = session.get("metadata", {}).get("client_name", "Unknown")
        tier = session.get("metadata", {}).get("tier", "standard")
        quota = TIER_LIMITS.get(tier, 5000)
        new_key = f"ann_{tier}_{uuid.uuid4().hex[:12]}"

        async with AsyncSessionLocal() as db:
            db.add(ClientAPIKey(
                client_name=client_name,
                api_key=new_key,
                plan_tier=tier,
                monthly_quota=quota,
            ))
            await db.commit()

    return {"status": "success"}
