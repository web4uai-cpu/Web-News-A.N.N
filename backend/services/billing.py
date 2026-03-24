"""
A.N.N. B2B Billing & Revenue Engine
Integrates with Stripe to handle enterprise API key purchases and subscriptions.
"""

import os
import stripe
import uuid
from fastapi import Request, HTTPException
from models.b2b_database import AsyncSessionLocal, ClientAPIKey
from utils.logger import get_logger

log = get_logger("billing")

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Mock product tracking (in a real app, these map to Stripe Price IDs)
TIER_LIMITS = {
    "standard": 5000,
    "pro": 25000,
    "enterprise": 100000
}

async def create_checkout_session(tier: str, client_name: str, success_url: str, cancel_url: str, currency: str = "usd"):
    """
    Generate a Stripe checkout session for a B2B API key purchase.
    Supports 'usd' and 'inr' currencies.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API keys are not configured.")

    if tier not in TIER_LIMITS:
        raise HTTPException(status_code=400, detail="Invalid plan tier.")

    try:
        # Define pricing based on currency (amount is in smallest currency unit: cents/paise)
        if currency.lower() == "inr":
            prices = {
                "standard": 399900,   # ₹3,999
                "pro": 1599900,       # ₹15,999
                "enterprise": 7999900 # ₹79,999
            }
        else:
            currency = "usd"
            prices = {
                "standard": 4900,     # $49.00
                "pro": 19900,         # $199.00
                "enterprise": 99900   # $999.00
            }

        amount = prices.get(tier, prices["standard"])
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": f"A.N.N. API - {tier.upper()} Tier",
                            "description": f"Provides up to {TIER_LIMITS[tier]} API requests per month.",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=client_name,
            metadata={"tier": tier, "client_name": client_name}
        )
        return {"checkout_url": session.url}
    except Exception as e:
        log.error("stripe_checkout_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create payment session.")

async def handle_stripe_webhook(payload: bytes, sig_header: str):
    """
    Securely process Stripe webhook events (e.g. successful payments).
    """
    if not STRIPE_WEBHOOK_SECRET:
        log.warning("stripe_webhook_ignored", reason="No webhook secret provided")
        return {"status": "ignored"}

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the checkout session being completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        client_name = session.get("metadata", {}).get("client_name", "Unknown Client")
        tier = session.get("metadata", {}).get("tier", "standard")
        quota = TIER_LIMITS.get(tier, 5000)

        new_api_key = f"ann_{tier}_{uuid.uuid4().hex[:12]}"

        try:
            async with AsyncSessionLocal() as db:
                new_client = ClientAPIKey(
                    client_name=client_name,
                    api_key=new_api_key,
                    plan_tier=tier,
                    monthly_quota=quota,
                )
                db.add(new_client)
                await db.commit()

            log.info("payment_success", tier=tier, client=client_name, new_key=new_api_key)
            # In production, dispatch an email to the client with their new API Key!
        except Exception as e:
            log.error("database_insertion_failed", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to provision API Key after payment.")

    return {"status": "success"}
