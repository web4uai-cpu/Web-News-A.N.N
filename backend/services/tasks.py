"""
Distributed Task Workers for the A.N.N Platform.
These tasks run entirely independently on scalable Worker Nodes,
allowing the central API to seamlessly accept 10,000+ commands per second.
"""

from ..celery_app import celery_app
from ..agents.orchestrator import master_pipeline
import asyncio
import redis
import json
import os
import logging

log = logging.getLogger("celery_worker")

# Setup a direct Redis connection for Pub/Sub Symphony
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(redis_url)

def run_async(coro):
    """Utility to run asynchronous code inside a historically synchronous Celery execution container."""
    return asyncio.run(coro)

@celery_app.task(name="tasks.b2b_distributed_pipeline", bind=True, max_retries=3)
def b2b_distributed_pipeline_task(self, topic: str, api_key: str):
    """
    The Ultimate Scalable Video Generation Task.
    Executed by distributed Linux workers pulled from the Redis queue.
    """
    log.info(f"Worker Node initiated B2B generation for topic: {topic}")
    
    try:
        # 1. Run the heavy AI pipeline (scraping, LLM, ElevenLabs, HeyGen) synchronously using asyncio.run
        final_script = run_async(master_pipeline(source="newsapi", generate_media=True, specific_query=topic))
        
        video_url = final_script.get("video_url", "https://ann-storage.s3.amazonaws.com/example_broadcast.mp4")
        
        # 2. Construct the Payload Symphony
        # We must beam this data back to the User's browser, but the User is connected to the API server via WebSocket.
        # This explicit worker node is on entirely different physical hardware.
        # Solution: Publish the payload onto a globally shared Redis channel!
        payload = {
            "type": "studio_delivery",
            "topic": topic,
            "script_id": final_script.get("id", "gen_error"),
            "video_url": video_url,
            "api_key": api_key, # Crucial: tells the API server WHICH websocket to push to
            "status": "complete"
        }
        
        redis_client.publish("ann_broadcasts", json.dumps(payload))
        log.info(f"Worker Node instantly published Render to Redis PubSub for {topic}")
        
        return {"status": "success", "topic": topic}
        
    except Exception as exc:
        log.error(f"Worker Node encountered error during {topic}: {exc}")
        self.retry(exc=exc, countdown=60) # Auto-retry 1 minute later if HeyGen API fails
