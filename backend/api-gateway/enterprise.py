"""
A.N.N. Enterprise API Service
Manages enterprise tiers, usage analytics, webhook filtering, and historical backfill.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from utils.logger import get_logger

log = get_logger("enterprise")


class EnterpriseTier(str, Enum):
    GROWTH = "growth"
    SCALE = "scale"
    UNLIMITED = "unlimited"
    WHITE_LABEL = "white_label"


ENTERPRISE_CONFIG = {
    EnterpriseTier.GROWTH: {
        "price_monthly": 499_00,
        "requests_per_month": 100_000,
        "sla": "99.9%",
        "support": "email",
        "dedicated_workers": False,
        "historical_days": 30,
    },
    EnterpriseTier.SCALE: {
        "price_monthly": 1_999_00,
        "requests_per_month": 500_000,
        "sla": "99.95%",
        "support": "priority",
        "dedicated_workers": True,
        "historical_days": 90,
    },
    EnterpriseTier.UNLIMITED: {
        "price_monthly": 4_999_00,
        "requests_per_month": -1,
        "sla": "99.99%",
        "support": "dedicated_csm",
        "dedicated_workers": True,
        "historical_days": 365,
    },
    EnterpriseTier.WHITE_LABEL: {
        "price_monthly": 9_999_00,
        "requests_per_month": -1,
        "sla": "99.99%",
        "support": "dedicated_csm",
        "dedicated_workers": True,
        "historical_days": 365,
    },
}


class EnterpriseClient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    tier: EnterpriseTier
    api_key: str = Field(default_factory=lambda: f"ann_ent_{uuid4().hex[:24]}")
    contact_email: str
    webhook_url: str | None = None
    webhook_categories: list[str] = Field(default_factory=list)
    webhook_keywords: list[str] = Field(default_factory=list)
    requests_this_month: int = 0
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UsageRecord(BaseModel):
    client_id: str
    endpoint: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    response_ms: float = 0.0
    status_code: int = 200


class WhiteLabelConfig(BaseModel):
    client_id: str
    subdomain: str
    brand_name: str
    logo_url: str = ""
    primary_color: str = "#6366f1"
    secondary_color: str = "#22d3ee"
    font_family: str = "Inter"
    voice_id: str = ""
    avatar_id: str = ""


class EnterpriseService:
    def __init__(self):
        self._clients: dict[str, EnterpriseClient] = {}
        self._usage: list[UsageRecord] = []
        self._white_label: dict[str, WhiteLabelConfig] = {}

    def create_client(self, client: EnterpriseClient) -> EnterpriseClient:
        self._clients[client.id] = client
        log.info("enterprise_client_created", client_id=client.id, tier=client.tier.value)
        return client

    def check_quota(self, client_id: str) -> bool:
        client = self._clients.get(client_id)
        if not client:
            return False
        config = ENTERPRISE_CONFIG[client.tier]
        limit = config["requests_per_month"]
        return limit == -1 or client.requests_this_month < limit

    def record_usage(self, record: UsageRecord) -> None:
        self._usage.append(record)
        client = self._clients.get(record.client_id)
        if client:
            client.requests_this_month += 1

    def get_usage_stats(self, client_id: str) -> dict:
        client_usage = [u for u in self._usage if u.client_id == client_id]
        return {
            "total_requests": len(client_usage),
            "avg_response_ms": (
                sum(u.response_ms for u in client_usage) / len(client_usage)
                if client_usage else 0
            ),
            "error_rate": (
                sum(1 for u in client_usage if u.status_code >= 500) / len(client_usage)
                if client_usage else 0
            ),
        }

    def should_send_webhook(self, client: EnterpriseClient, category: str, text: str) -> bool:
        if not client.webhook_url:
            return False
        if client.webhook_categories and category not in client.webhook_categories:
            return False
        if client.webhook_keywords:
            text_lower = text.lower()
            return any(kw.lower() in text_lower for kw in client.webhook_keywords)
        return True

    def set_white_label(self, config: WhiteLabelConfig) -> WhiteLabelConfig:
        self._white_label[config.client_id] = config
        log.info("white_label_configured", client_id=config.client_id, subdomain=config.subdomain)
        return config

    def get_white_label(self, client_id: str) -> WhiteLabelConfig | None:
        return self._white_label.get(client_id)
