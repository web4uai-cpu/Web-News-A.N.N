"""
HTTP reverse proxy — forwards requests to downstream microservices.
"""

import httpx
from fastapi import Request, Response
from routes import Route


_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
    return _client


async def close_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def proxy_request(request: Request, route: Route) -> Response:
    """Forward an incoming request to the matched upstream service."""
    client = await get_client()

    # Build upstream URL
    path = request.url.path
    if route.strip_prefix:
        path = path[len(route.prefix):]
        if not path.startswith("/"):
            path = "/" + path

    upstream_url = f"{route.upstream}{path}"
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    # Forward headers (strip hop-by-hop)
    headers = dict(request.headers)
    for hop_header in ("host", "connection", "transfer-encoding", "keep-alive"):
        headers.pop(hop_header, None)

    # Read body
    body = await request.body()

    try:
        upstream_response = await client.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            content=body if body else None,
        )

        # Build response, forwarding status + headers + body
        response_headers = dict(upstream_response.headers)
        for h in ("content-encoding", "content-length", "transfer-encoding"):
            response_headers.pop(h, None)

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=response_headers,
            media_type=upstream_response.headers.get("content-type"),
        )

    except httpx.ConnectError:
        return Response(
            content=f'{{"detail": "Service unavailable: {route.upstream}"}}',
            status_code=503,
            media_type="application/json",
        )
    except httpx.TimeoutException:
        return Response(
            content='{"detail": "Upstream service timeout"}',
            status_code=504,
            media_type="application/json",
        )
