"""Editorial + ingestion + pipeline routes (all cost-sensitive — auth-gated)."""

import os
import sys

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from core import runtime
from core.security import require_pipeline_access
from models.schemas import (
    ArticleInput,
    BroadcastScript,
    FinancialIngestRequest,
    IngestRequest,
    PipelineStatus,
)
from services.queue_manager import queue_manager
from services.realtime import ws_manager
from utils.logger import get_logger

router = APIRouter()
log = get_logger("pipeline_router")


# ── Single Article Processing ──────────────────────────

@router.post("/api/v1/process_news", response_model=BroadcastScript, tags=["Editorial"])
async def process_raw_news(article: ArticleInput, _auth: dict = Depends(require_pipeline_access)):
    """
    Process a single raw article through the editorial pipeline.

    Steps:
    1. Extract facts (copyright compliance)
    2. Write original English broadcast script
    3. Generate headline
    4. Translate to Hindi
    """
    try:
        script = await runtime.pipeline.process_single_article(article)
        await runtime.store_script(script)

        # World-Class Real-Time Push
        try:
            await ws_manager.broadcast_news(script.model_dump())
        except Exception as e:
            log.error("websocket_broadcast_failed", error=str(e))

        return script
    except Exception as e:
        log.error("process_news_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ── Ingestion Endpoints ───────────────────────────────

@router.post("/api/v1/ingest/newsapi", response_model=list[BroadcastScript], tags=["Ingestion"])
async def ingest_from_newsapi(request: IngestRequest, _auth: dict = Depends(require_pipeline_access)):
    """Fetch articles from NewsAPI, process through editorial pipeline."""
    try:
        articles = await runtime.newsapi.fetch_articles(
            category=request.category.value,
            query=request.query,
            max_articles=request.max_articles,
        )
        if not articles:
            raise HTTPException(status_code=404, detail="No articles found.")

        scripts = []
        for article in articles:
            try:
                script = await runtime.pipeline.process_single_article(article)
                await runtime.store_script(script)
                scripts.append(script)
            except Exception as e:
                log.error("article_failed", url=article.source_url, error=str(e))

        return scripts
    except HTTPException:
        raise
    except Exception as e:
        log.error("newsapi_ingest_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/ingest/financial", response_model=list[BroadcastScript], tags=["Ingestion"])
async def ingest_financial_news(request: FinancialIngestRequest, _auth: dict = Depends(require_pipeline_access)):
    """Fetch financial news from Alpha Vantage, process through pipeline."""
    try:
        tickers = ",".join(request.symbols)
        articles = await runtime.alphavantage.fetch_articles(
            category="finance",
            query=tickers,
            max_articles=request.max_articles,
        )
        if not articles:
            raise HTTPException(status_code=404, detail="No financial articles found.")

        scripts = []
        for article in articles:
            try:
                script = await runtime.pipeline.process_single_article(article)
                await runtime.store_script(script)
                scripts.append(script)
            except Exception as e:
                log.error("financial_article_failed", error=str(e))

        return scripts
    except HTTPException:
        raise
    except Exception as e:
        log.error("financial_ingest_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/ingest/gdelt", response_model=list[BroadcastScript], tags=["Ingestion"])
async def ingest_from_gdelt(request: IngestRequest, _auth: dict = Depends(require_pipeline_access)):
    """Fetch geopolitical events from GDELT, process through pipeline."""
    try:
        articles = await runtime.gdelt.fetch_articles(
            category=request.category.value,
            query=request.query,
            max_articles=request.max_articles,
        )
        if not articles:
            raise HTTPException(status_code=404, detail="No GDELT articles found.")

        scripts = []
        for article in articles:
            try:
                script = await runtime.pipeline.process_single_article(article)
                await runtime.store_script(script)
                scripts.append(script)
            except Exception as e:
                log.error("gdelt_article_failed", error=str(e))

        return scripts
    except HTTPException:
        raise
    except Exception as e:
        log.error("gdelt_ingest_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def _fetch_from_source(source: str, request: IngestRequest):
    if source == "financial":
        return await runtime.alphavantage.fetch_articles(max_articles=request.max_articles)
    if source == "gdelt":
        return await runtime.gdelt.fetch_articles(
            category=request.category.value, query=request.query, max_articles=request.max_articles,
        )
    return await runtime.newsapi.fetch_articles(
        category=request.category.value, query=request.query, max_articles=request.max_articles,
    )


# ── Full Pipeline ──────────────────────────────────────

@router.post("/api/v1/pipeline/run", tags=["Pipeline"])
async def run_pipeline(
    background_tasks: BackgroundTasks,
    request: IngestRequest = IngestRequest(),
    generate_media: bool = Query(False, description="Generate audio/video (costs apply)"),
    source: str = Query("newsapi", description="Source: newsapi, financial, gdelt"),
    _auth: dict = Depends(require_pipeline_access),
):
    """
    Run the full pipeline in the background.
    Returns a job ID for status tracking.
    """
    job = await queue_manager.create_job()

    async def _dispatch():
        try:
            articles = await _fetch_from_source(source, request)

            if not articles:
                await queue_manager.update_job(
                    job.job_id,
                    status=PipelineStatus.FAILED,
                    error="No articles found from source.",
                )
                return

            if os.getenv("REDIS_URL"):
                # Production: Send to robust Celery Worker over Redis
                from services.tasks import process_news_batch
                raw_arts = [art.model_dump() for art in articles]
                process_news_batch.delay(job.job_id, raw_arts, generate_media)
                log.info("job_dispatched_to_celery", job_id=job.job_id)
            else:
                async def _run_and_store():
                    result_job = await runtime.pipeline.run_full_pipeline(
                        articles=articles,
                        generate_media=generate_media,
                        job=job,
                    )
                    if result_job.scripts:
                        for script in result_job.scripts:
                            await runtime.store_script(script)
                        log.info("pipeline_scripts_stored", count=len(result_job.scripts))

                background_tasks.add_task(_run_and_store)
                log.info("job_dispatched_to_background", job_id=job.job_id)

        except Exception as e:
            log.error("pipeline_dispatch_failed", job_id=job.job_id, error=str(e))
            await queue_manager.update_job(job.job_id, status=PipelineStatus.FAILED, error=str(e))

    # Immediate non-blocking response to the client
    background_tasks.add_task(_dispatch)

    return {
        "job_id": job.job_id,
        "status": "queued",
        "message": "Pipeline started. Use /api/v1/pipeline/status/{job_id} to track progress.",
    }


@router.get("/api/v1/pipeline/status/{job_id}", tags=["Pipeline"])
async def get_pipeline_status(job_id: str):
    """Check the status of a pipeline job."""
    job = await queue_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.get("/api/v1/pipeline/jobs", tags=["Pipeline"])
async def list_pipeline_jobs(limit: int = Query(20, ge=1, le=100)):
    """List recent pipeline jobs."""
    jobs = await queue_manager.list_jobs(limit=limit)
    return jobs


# ── LangGraph Orchestrator Pipeline (Advanced Mode) ────

@router.post("/api/v1/pipeline/orchestrator", tags=["Pipeline"])
async def run_orchestrator_pipeline(
    background_tasks: BackgroundTasks,
    request: IngestRequest = IngestRequest(),
    source: str = Query("newsapi", description="Source: newsapi, financial, gdelt"),
    _auth: dict = Depends(require_pipeline_access),
):
    """
    Run the advanced LangGraph multi-agent orchestrator pipeline.
    Includes: discovery, fact-check, legal review, SEO, social broadcast, search indexing.
    """
    job = await queue_manager.create_job()

    async def _run_orchestrator():
        try:
            articles = await _fetch_from_source(source, request)

            if not articles:
                await queue_manager.update_job(job.job_id, status=PipelineStatus.FAILED, error="No articles found.")
                return

            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            orchestrator_dir = os.path.join(os.path.dirname(backend_dir), "agents", "orchestrator")
            if orchestrator_dir not in sys.path:
                sys.path.insert(0, orchestrator_dir)

            try:
                from runner import process_batch
                batch = [
                    {"raw_text": a.raw_text, "source_url": a.source_url, "source_name": a.source_name, "category": a.category.value}
                    for a in articles
                ]
                results = await process_batch(batch, concurrency=3)

                for state in results:
                    if state.headline and state.english_script:
                        script = BroadcastScript(
                            headline=state.headline,
                            english_script=state.english_script,
                            hindi_script=state.hindi_script,
                            translations=state.translations,
                            category=request.category,
                            source_url=state.source_url,
                        )
                        await runtime.store_script(script)

                await queue_manager.update_job(job.job_id, status=PipelineStatus.COMPLETED, progress_pct=100)
                log.info("orchestrator_pipeline_complete", job_id=job.job_id, articles=len(results))

            except ImportError as e:
                log.error("orchestrator_import_failed", error=str(e))
                await queue_manager.update_job(
                    job.job_id, status=PipelineStatus.FAILED,
                    error=f"LangGraph orchestrator not available: {str(e)}. Install langgraph: pip install langgraph",
                )

        except Exception as e:
            log.error("orchestrator_pipeline_failed", job_id=job.job_id, error=str(e))
            await queue_manager.update_job(job.job_id, status=PipelineStatus.FAILED, error=str(e))

    background_tasks.add_task(_run_orchestrator)
    return {
        "job_id": job.job_id,
        "status": "queued",
        "pipeline": "langgraph_orchestrator",
        "message": "Advanced orchestrator pipeline started. Includes discovery, legal, SEO, social broadcast.",
    }
