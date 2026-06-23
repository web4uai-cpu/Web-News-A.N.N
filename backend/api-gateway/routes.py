"""
Route registry — maps incoming request paths to downstream microservices.
During migration, unextracted routes fall through to the legacy monolith.
"""

from dataclasses import dataclass
from enum import Enum
from config import get_settings


class AuthLevel(str, Enum):
    NONE = "none"
    JWT = "jwt"
    API_KEY = "api_key"
    ADMIN = "admin"


@dataclass
class Route:
    prefix: str
    upstream: str
    auth: AuthLevel = AuthLevel.NONE
    strip_prefix: bool = False


def build_route_table() -> list[Route]:
    s = get_settings()

    return [
        # ── Auth Service ──────────────────────────────────
        Route("/api/v1/auth/", s.auth_service_url, AuthLevel.NONE),
        Route("/api/v1/admin/clients", s.auth_service_url, AuthLevel.ADMIN),
        Route("/api/v1/admin/settings", s.auth_service_url, AuthLevel.ADMIN),

        # ── Article Service ───────────────────────────────
        Route("/api/v1/scripts", s.article_service_url, AuthLevel.NONE),
        Route("/api/v1/process_news", s.article_service_url, AuthLevel.NONE),
        Route("/feed/", s.article_service_url, AuthLevel.NONE),
        Route("/embed/", s.article_service_url, AuthLevel.NONE),
        Route("/api/v1/b2b/feed/", s.article_service_url, AuthLevel.API_KEY),

        # ── Pipeline (article-service) ────────────────────
        Route("/api/v1/pipeline/", s.article_service_url, AuthLevel.NONE),

        # ── Dashboard (analytics-service) ─────────────────
        Route("/api/v1/dashboard/", s.analytics_service_url, AuthLevel.NONE),

        # ── Video Service ─────────────────────────────────
        Route("/api/v1/media/", s.video_service_url, AuthLevel.NONE),

        # ── Notification Service ──────────────────────────
        Route("/api/v1/social/", s.notification_service_url, AuthLevel.NONE),

        # ── B2B Portal ────────────────────────────────────
        Route("/api/v1/b2b/checkout", s.auth_service_url, AuthLevel.NONE),
        Route("/api/v1/b2b/portal/", s.auth_service_url, AuthLevel.API_KEY),
        Route("/api/v1/webhooks/stripe", s.auth_service_url, AuthLevel.NONE),

        # ── Analytics Service ─────────────────────────────
        Route("/api/v1/analytics/", s.analytics_service_url, AuthLevel.NONE),

        # ── Search Service ────────────────────────────────
        Route("/api/v1/search/", s.search_service_url, AuthLevel.NONE),
    ]


def resolve_route(path: str) -> Route | None:
    """Find the most specific matching route for a given path."""
    routes = build_route_table()
    best: Route | None = None
    best_len = 0

    for route in routes:
        if path.startswith(route.prefix) and len(route.prefix) > best_len:
            best = route
            best_len = len(route.prefix)

    return best
