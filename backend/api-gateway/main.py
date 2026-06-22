"""
A.N.N. API Gateway
Central entry point for all client requests. Routes traffic to downstream microservices
with authentication, rate limiting, and observability.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from routes import resolve_route, AuthLevel
from proxy import proxy_request, close_client
from middleware import apply_auth, apply_rate_limit
from rate_limiter import close_redis

settings = get_settings()
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_client()
    await close_redis()


app = FastAPI(
    title="A.N.N. API Gateway",
    description="Central routing layer for the AI News Network microservices.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics (optional)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
except ImportError:
    pass


# ── Health Check ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "service": "api-gateway",
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


# ── Catch-All Proxy ──────────────────────────────────────

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def gateway_proxy(request: Request, path: str):
    full_path = f"/{path}"

    # 1. Resolve route
    route = resolve_route(full_path)

    if route is None:
        # Fallback to monolith for unmapped routes
        from routes import Route
        route = Route(
            prefix="/",
            upstream=settings.monolith_url,
            auth=AuthLevel.NONE,
        )

    # 2. Rate limiting
    rate_limit_error = await apply_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    # 3. Auth check
    auth_error = await apply_auth(request, route)
    if auth_error:
        return auth_error

    # 4. Proxy to upstream
    response = await proxy_request(request, route)

    # 5. Attach rate limit headers
    if hasattr(request.state, "rate_limit_headers"):
        for k, v in request.state.rate_limit_headers.items():
            response.headers[k] = v

    return response


# ── WebSocket Proxy ───────────────────────────────────────

@app.websocket("/ws/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    """Proxy WebSocket connections to the monolith (or notification service)."""
    import httpx
    import asyncio

    await websocket.accept()

    ws_url = f"{settings.monolith_url.replace('http', 'ws')}/ws/{path}"
    if websocket.query_params:
        ws_url += f"?{websocket.query_params}"

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", ws_url.replace("ws", "http")) as _:
                pass
    except Exception:
        pass

    # For now, keep connection open and relay from monolith
    # Full WebSocket proxy requires websockets library — deferred to Sprint 5
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass


# ── Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
