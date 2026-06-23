"""
A.N.N. Public Status Page API
Exposes service health and incident status for the public status page.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import httpx

from utils.logger import get_logger
from config import get_settings

log = get_logger("status_page")


class ServiceStatus(str, Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceHealth:
    name: str
    status: ServiceStatus = ServiceStatus.OPERATIONAL
    latency_ms: float = 0.0
    last_checked: str = ""
    uptime_pct: float = 100.0


@dataclass
class Incident:
    id: str
    title: str
    status: str
    severity: str
    created_at: str
    updated_at: str
    components: list[str] = field(default_factory=list)
    updates: list[dict] = field(default_factory=list)


SERVICES = {
    "api-gateway": {"url": "http://api-gateway:8000/health", "display": "API Gateway"},
    "auth-service": {"url": "http://auth-service:8001/health", "display": "Authentication"},
    "article-service": {"url": "http://article-service:8002/health", "display": "Article Service"},
    "video-service": {"url": "http://video-service:8003/health", "display": "Video Service"},
    "notification-service": {"url": "http://notification-service:8004/health", "display": "Notifications"},
    "analytics-service": {"url": "http://analytics-service:8005/health", "display": "Analytics"},
    "search-service": {"url": "http://search-service:8006/health", "display": "Search"},
}


class StatusChecker:
    def __init__(self):
        self._history: dict[str, list[bool]] = {k: [] for k in SERVICES}

    async def check_service(self, name: str, config: dict) -> ServiceHealth:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(config["url"])
                latency = (time.monotonic() - start) * 1000
                ok = resp.status_code == 200
        except Exception:
            latency = (time.monotonic() - start) * 1000
            ok = False

        self._history[name].append(ok)
        if len(self._history[name]) > 1440:
            self._history[name] = self._history[name][-1440:]

        checks = self._history[name]
        uptime = (sum(checks) / len(checks) * 100) if checks else 100.0

        if not ok:
            status = ServiceStatus.MAJOR_OUTAGE
        elif latency > 500:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.OPERATIONAL

        return ServiceHealth(
            name=config["display"],
            status=status,
            latency_ms=round(latency, 1),
            last_checked=datetime.now(timezone.utc).isoformat(),
            uptime_pct=round(uptime, 2),
        )

    async def check_all(self) -> list[ServiceHealth]:
        results = []
        for name, config in SERVICES.items():
            health = await self.check_service(name, config)
            results.append(health)
        return results

    def overall_status(self, services: list[ServiceHealth]) -> ServiceStatus:
        statuses = [s.status for s in services]
        if ServiceStatus.MAJOR_OUTAGE in statuses:
            return ServiceStatus.MAJOR_OUTAGE
        if ServiceStatus.PARTIAL_OUTAGE in statuses:
            return ServiceStatus.PARTIAL_OUTAGE
        if ServiceStatus.DEGRADED in statuses:
            return ServiceStatus.DEGRADED
        return ServiceStatus.OPERATIONAL


status_checker = StatusChecker()
