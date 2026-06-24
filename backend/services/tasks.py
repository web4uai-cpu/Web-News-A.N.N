"""
Distributed Task Workers for the A.N.N Platform.
These tasks run entirely independently on scalable Worker Nodes,
allowing the central API to seamlessly accept 10,000+ commands per second.
"""

from celery_app import celery_app
import asyncio
import json
import os
import logging

log = logging.getLogger("celery_worker")

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def _get_redis_client():
    import redis
    return redis.Redis.from_url(redis_url)


@celery_app.task(name="tasks.b2b_distributed_pipeline", bind=True, max_retries=3)
def b2b_distributed_pipeline_task(self, topic: str, api_key: str):
    """Runs the AI pipeline for a B2B on-demand generation request."""
    log.info(f"Worker Node initiated B2B generation for topic: {topic}")

    try:
        from services.pipeline import NewsPipeline
        from models.schemas import ArticleInput, NewsCategory

        pipeline = NewsPipeline()
        article = ArticleInput(
            title=topic,
            raw_text=f"Generate a comprehensive news broadcast about: {topic}",
            source_name="B2B Studio",
            source_url="",
            category=NewsCategory.GENERAL,
        )
        script = asyncio.run(pipeline.process_single_article(article))

        payload = {
            "type": "studio_delivery",
            "topic": topic,
            "script_id": getattr(script, "id", "gen_error"),
            "video_url": getattr(script, "video_url", ""),
            "api_key": api_key,
            "status": "complete",
        }

        _get_redis_client().publish("ann_broadcasts", json.dumps(payload))
        log.info(f"Worker Node published result to Redis PubSub for {topic}")

        return {"status": "success", "topic": topic}

    except Exception as exc:
        log.error(f"Worker Node encountered error during {topic}: {exc}")
        self.retry(exc=exc, countdown=60)
