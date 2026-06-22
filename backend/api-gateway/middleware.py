"""
Gateway middleware — auth validation and rate limiting applied before proxying.
"""

from fastapi import Request, Response
from routes import AuthLevel, Route
from rate_limiter import check_rate_limit
from config import get_settings
import os


async def apply_auth(request: Request, route: Route) -> Response | None:
    """
    Validate authentication based on route's auth level.
    Returns an error Response if auth fails, or None if auth passes.
    """
    if route.auth == AuthLevel.NONE:
        return None

    if route.auth == AuthLevel.API_KEY:
        api_key = request.headers.get("x-ann-api-key")
        if not api_key:
            return Response(
                content='{"detail": "B2B API Key is missing. Pass X-ANN-API-Key header."}',
                status_code=401,
                media_type="application/json",
            )
        # Key validation delegated to auth-service; gateway just checks presence
        return None

    if route.auth == AuthLevel.ADMIN:
        admin_token = request.headers.get("x-admin-token")
        expected = os.getenv("ADMIN_SECRET", "superadmin123")
        if admin_token != expected:
            return Response(
                content='{"detail": "Invalid Admin Token"}',
                status_code=403,
                media_type="application/json",
            )
        return None

    if route.auth == AuthLevel.JWT:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content='{"detail": "Missing or invalid Authorization header"}',
                status_code=401,
                media_type="application/json",
            )
        # JWT verification delegated to auth-service
        return None

    return None


async def apply_rate_limit(request: Request) -> Response | None:
    """
    Apply inbound rate limiting. Returns 429 Response if exceeded, None if allowed.
    """
    settings = get_settings()

    # Determine rate limit key and limit
    api_key = request.headers.get("x-ann-api-key")
    if api_key:
        key = f"key:{api_key}"
        limit = settings.rate_limit_authenticated_rpm
    else:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"
        limit = settings.rate_limit_anonymous_rpm

    allowed, remaining = await check_rate_limit(key, limit)

    if not allowed:
        return Response(
            content='{"detail": "Rate limit exceeded. Please slow down."}',
            status_code=429,
            media_type="application/json",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "60",
            },
        )

    # Attach rate limit headers (will be added to proxied response)
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
    }
    return None
