"""
A.N.N. Auth Service
Handles user authentication, B2B API key management, billing, and admin settings.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from api_keys import router as api_keys_router
from billing import router as billing_router
from settings_admin import router as settings_router

settings = get_settings()
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="A.N.N. Auth Service",
    description="Authentication, API key management, and billing for the AI News Network.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api_keys_router)
app.include_router(billing_router)
app.include_router(settings_router)


@app.get("/health")
async def health():
    return {
        "service": "auth-service",
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
