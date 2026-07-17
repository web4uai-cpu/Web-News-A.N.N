"""
A.N.N. Shared Runtime
Singletons shared across routers: the in-memory script store, service clients,
and the store_script persistence helper. Import from here — do not re-instantiate.
"""

import time

from config import get_settings
from ingestion.alphavantage_source import AlphaVantageSource
from ingestion.gdelt_source import GDELTSource
from ingestion.newsapi_source import NewsAPISource
from media.elevenlabs_tts import ElevenLabsTTS
from media.heygen_video import HeyGenVideoGenerator
from models.schemas import BroadcastScript
from services.pipeline import NewsPipeline
from social.social_scheduler import SocialScheduler
from utils.logger import get_logger

log = get_logger("runtime")
settings = get_settings()

START_TIME = time.time()

# In-memory script cache (backed by the DB; reloaded on startup)
script_store: dict[str, BroadcastScript] = {}

social_scheduler = SocialScheduler(base_url=settings.public_url)
pipeline = NewsPipeline()
newsapi = NewsAPISource()
alphavantage = AlphaVantageSource()
gdelt = GDELTSource()
tts_service = ElevenLabsTTS()
video_service = HeyGenVideoGenerator()


async def store_script(script: BroadcastScript):
    """Store script in memory, persist to database, and auto-post to social media."""
    script_store[script.id] = script
    from models.b2b_database import save_script_to_db
    try:
        await save_script_to_db(script.model_dump())
    except Exception as e:
        log.error("script_db_save_failed", script_id=script.id, error=str(e))

    if settings.social_auto_post:
        try:
            result = await social_scheduler.broadcast(script)
            log.info("social_auto_posted", script_id=script.id, platforms=result.get("platforms", {}))
        except Exception as e:
            log.error("social_auto_post_failed", script_id=script.id, error=str(e))

    # Notify B2B clients (HMAC-signed, fire-and-forget)
    try:
        import asyncio
        from services.webhooks import broadcast_event
        asyncio.create_task(broadcast_event("script.created", {
            "id": script.id,
            "headline": script.headline,
            "category": script.category.value if hasattr(script.category, "value") else script.category,
            "created_at": script.created_at,
        }))
    except Exception as e:
        log.error("webhook_dispatch_failed", script_id=script.id, error=str(e))


def sorted_scripts() -> list[BroadcastScript]:
    return sorted(script_store.values(), key=lambda s: s.created_at, reverse=True)
