"""Social media broadcast + status endpoints."""

from fastapi import APIRouter, HTTPException

from config import get_settings
from core import runtime

router = APIRouter()
settings = get_settings()


@router.post("/api/v1/social/broadcast/{script_id}", tags=["Social Media"])
async def broadcast_to_social(script_id: str):
    """Manually broadcast a script to all configured social media platforms."""
    script = runtime.script_store.get(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")
    result = await runtime.social_scheduler.broadcast(script)
    return result


@router.get("/api/v1/social/status", tags=["Social Media"])
async def social_status():
    """Check which social media platforms are configured."""
    scheduler = runtime.social_scheduler
    return {
        "enabled_platforms": scheduler.enabled_platforms,
        "auto_post": settings.social_auto_post,
        "platforms": {
            "twitter": {"enabled": scheduler.twitter.enabled},
            "facebook": {"enabled": scheduler.facebook.enabled},
            "instagram": {"enabled": scheduler.instagram.enabled},
        },
    }


@router.post("/api/v1/social/test/{platform}", tags=["Social Media"])
async def test_social_connection(platform: str):
    """Test if a social media platform's credentials are valid."""
    scheduler = runtime.social_scheduler
    if platform == "twitter":
        if not scheduler.twitter.enabled:
            return {"status": "error", "message": "Twitter bearer token not configured"}
        return {"status": "ok", "message": "Twitter credentials configured"}
    elif platform == "facebook":
        if not scheduler.facebook.enabled:
            return {"status": "error", "message": "Facebook page token not configured"}
        return {"status": "ok", "message": "Facebook credentials configured"}
    elif platform == "instagram":
        if not scheduler.instagram.enabled:
            return {"status": "error", "message": "Instagram access token not configured"}
        return {"status": "ok", "message": "Instagram credentials configured"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
