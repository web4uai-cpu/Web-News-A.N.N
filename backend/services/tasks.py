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


@celery_app.task(name="tasks.process_news_batch", bind=True, max_retries=3)
def process_news_batch(self, job_id: str, raw_articles: list, generate_media: bool = False):
    """
    Run the full editorial pipeline over a batch of ingested articles on a
    Worker Node. Mirrors the in-process ``_run_and_store`` branch in
    ``routers/pipeline.py`` so production (REDIS_URL set) and local dev behave
    identically. Persists each resulting script and pushes it to the
    ``ann_broadcasts`` channel for the WebSocket bridge.
    """
    log.info(f"Worker Node processing news batch job={job_id} count={len(raw_articles)}")

    try:
        from core import runtime
        from models.schemas import ArticleInput

        articles = [ArticleInput(**art) for art in raw_articles]

        async def _run_and_store() -> list:
            result_job = await runtime.pipeline.run_full_pipeline(
                articles=articles,
                generate_media=generate_media,
            )
            for script in result_job.scripts:
                await runtime.store_script(script)
            return result_job.scripts

        scripts = asyncio.run(_run_and_store())

        client = _get_redis_client()
        for script in scripts:
            client.publish("ann_broadcasts", json.dumps({
                "type": "breaking_news",
                "job_id": job_id,
                **script.model_dump(mode="json"),
            }))

        log.info(f"Worker Node stored {len(scripts)} scripts for job={job_id}")
        return {"status": "success", "job_id": job_id, "scripts": len(scripts)}

    except Exception as exc:
        log.error(f"Worker Node failed news batch job={job_id}: {exc}")
        self.retry(exc=exc, countdown=60)
