"""
A.N.N. Subscription & Premium Service
Stripe subscription management, tier gating, and referral program.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from utils.logger import get_logger
from config import get_settings

log = get_logger("subscriptions")


class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    CREATOR = "creator"
    BUSINESS_PRO = "business_pro"
    ENTERPRISE = "enterprise"


TIER_CONFIG = {
    SubscriptionTier.FREE: {
        "price_monthly": 0,
        "articles_per_day": 3,
        "api_requests": 0,
        "audio_access": False,
        "video_access": False,
        "ads": True,
    },
    SubscriptionTier.STARTER: {
        "price_monthly": 9_99,
        "articles_per_day": -1,
        "api_requests": 0,
        "audio_access": False,
        "video_access": False,
        "ads": False,
    },
    SubscriptionTier.CREATOR: {
        "price_monthly": 29_99,
        "articles_per_day": -1,
        "api_requests": 0,
        "audio_access": True,
        "video_access": True,
        "ads": False,
    },
    SubscriptionTier.BUSINESS_PRO: {
        "price_monthly": 199_00,
        "articles_per_day": -1,
        "api_requests": 50_000,
        "audio_access": True,
        "video_access": True,
        "ads": False,
    },
    SubscriptionTier.ENTERPRISE: {
        "price_monthly": 0,
        "articles_per_day": -1,
        "api_requests": -1,
        "audio_access": True,
        "video_access": True,
        "ads": False,
    },
}


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    tier: SubscriptionTier = SubscriptionTier.FREE
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    status: str = "active"
    current_period_end: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Referral(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    referrer_id: str
    referred_id: str | None = None
    code: str = Field(default_factory=lambda: str(uuid4())[:8])
    redeemed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SubscriptionService:
    def __init__(self):
        self.settings = get_settings()

    def check_article_access(self, tier: SubscriptionTier, articles_read_today: int) -> bool:
        config = TIER_CONFIG[tier]
        limit = config["articles_per_day"]
        return limit == -1 or articles_read_today < limit

    def check_feature_access(self, tier: SubscriptionTier, feature: str) -> bool:
        config = TIER_CONFIG[tier]
        return config.get(feature, False)

    def shows_ads(self, tier: SubscriptionTier) -> bool:
        return TIER_CONFIG[tier]["ads"]

    async def create_checkout_session(
        self, user_id: str, tier: SubscriptionTier, success_url: str, cancel_url: str
    ) -> dict:
        stripe_prices = {
            SubscriptionTier.STARTER: "price_starter_monthly",
            SubscriptionTier.CREATOR: "price_creator_monthly",
            SubscriptionTier.BUSINESS_PRO: "price_business_pro_monthly",
        }

        price_id = stripe_prices.get(tier)
        if not price_id:
            return {"error": f"No Stripe price for tier: {tier.value}"}

        log.info("creating_checkout", user_id=user_id, tier=tier.value)

        return {
            "checkout_url": f"https://checkout.stripe.com/c/pay/{price_id}",
            "session_id": str(uuid4()),
            "tier": tier.value,
        }

    async def create_billing_portal(self, stripe_customer_id: str, return_url: str) -> dict:
        log.info("creating_billing_portal", customer_id=stripe_customer_id)
        return {
            "portal_url": f"https://billing.stripe.com/p/session/{stripe_customer_id}",
        }

    def generate_referral_code(self, user_id: str) -> Referral:
        referral = Referral(referrer_id=user_id)
        log.info("referral_created", referrer_id=user_id, code=referral.code)
        return referral
