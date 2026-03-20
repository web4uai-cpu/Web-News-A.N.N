"""
A.N.N. Queue Manager
In-memory job queue for MVP. In production, replace with Redis/Kafka.
"""

import asyncio
from datetime import datetime
from models.schemas import PipelineJob, PipelineStatus
from utils.logger import get_logger

log = get_logger("queue_manager")


class QueueManager:
    """
    In-memory job queue and state tracker.
    
    For the MVP, this provides simple job tracking without external
    dependencies. In production, this should be backed by Redis
    or a proper message queue like Kafka.
    """

    def __init__(self):
        self._jobs: dict[str, PipelineJob] = {}
        self._lock = asyncio.Lock()

    async def create_job(self) -> PipelineJob:
        """Create a new pipeline job."""
        async with self._lock:
            job = PipelineJob()
            self._jobs[job.job_id] = job
            log.info("job_created", job_id=job.job_id)
            return job

    async def update_job(
        self,
        job_id: str,
        status: PipelineStatus | None = None,
        progress_pct: int | None = None,
        error: str | None = None,
    ) -> PipelineJob | None:
        """Update a job's status."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            if status:
                job.status = status
            if progress_pct is not None:
                job.progress_pct = progress_pct
            if error:
                job.errors.append(error)
            if status in (PipelineStatus.COMPLETED, PipelineStatus.FAILED):
                job.completed_at = datetime.utcnow()

            log.info(
                "job_updated",
                job_id=job_id,
                status=job.status.value,
                progress=job.progress_pct,
            )
            return job

    async def get_job(self, job_id: str) -> PipelineJob | None:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    async def list_jobs(self, limit: int = 20) -> list[PipelineJob]:
        """List recent jobs, newest first."""
        sorted_jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.started_at,
            reverse=True,
        )
        return sorted_jobs[:limit]

    @property
    def active_count(self) -> int:
        """Count of currently running jobs."""
        return sum(
            1
            for j in self._jobs.values()
            if j.status not in (PipelineStatus.COMPLETED, PipelineStatus.FAILED)
        )


# ── Global singleton ────────────────────────────────────
queue_manager = QueueManager()
