"""
A.N.N. Enterprise Celery Architecture
Distributed task queue for high-availability pipeline execution.
"""

import os
from celery import Celery
from config import get_settings

settings = get_settings()

# Read Redis URL for broker and result backend (fallback to local if running in Docker)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ann_worker",
    broker=redis_url,
    backend=redis_url,
    include=["services.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
)

if __name__ == "__main__":
    celery_app.start()
