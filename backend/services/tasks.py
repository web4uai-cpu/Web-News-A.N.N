"""
A.N.N. Distributed Architecture Tasks
Defines the Celery workers that execute the pipeline jobs asynchronously.
"""

from celery_app import celery_app
from services.pipeline import NewsPipeline
from models.schemas import ArticleInput
from services.queue_manager import queue_manager
import asyncio
from utils.logger import get_logger

log = get_logger("celery_tasks")

# Because Celery doesn't natively support asyncio without specific extensions,
# we use asyncio.run to execute the async pipeline in the sync Celery context.
@celery_app.task(bind=True, name="tasks.process_news_batch")
def process_news_batch(self, job_id: str, raw_articles: list[dict], generate_media: bool):
    """
    Background worker task to process an entire batch of news.
    """
    log.info("celery_worker_starting_job", job_id=job_id)
    
    # Reconstruct Pydantic models from Celery JSON payload
    articles = [ArticleInput(**art) for art in raw_articles]
    
    # Initialize pipeline
    pipeline = NewsPipeline()
    
    async def _run():
        job = await queue_manager.get_job(job_id)
        if job:
            await pipeline.run_full_pipeline(articles, generate_media, job)
        else:
            log.error("celery_worker_job_not_found", job_id=job_id)

    # Execute async pipeline blocking this worker until done
    asyncio.run(_run())
    
    return f"Completed job {job_id}"
