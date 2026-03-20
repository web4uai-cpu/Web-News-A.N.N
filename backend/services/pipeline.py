"""
A.N.N. Pipeline Orchestrator
Full news-to-broadcast pipeline: Ingest → Extract → Script → Translate → Audio → Video.
"""

import asyncio
from models.schemas import (
    ArticleInput,
    BroadcastScript,
    ExtractedFacts,
    PipelineJob,
    PipelineStatus,
    NewsCategory,
    Language,
)
from agents.fact_extractor import FactExtractorAgent
from agents.scriptwriter import ScriptwriterAgent
from agents.translator import TranslatorAgent
from agents.headline_generator import HeadlineGeneratorAgent
from agents.critic import CriticAgent
from media.elevenlabs_tts import ElevenLabsTTS
from media.heygen_video import HeyGenVideoGenerator
from services.queue_manager import queue_manager
from utils.logger import get_logger

log = get_logger("pipeline")


class NewsPipeline:
    """
    Orchestrates the full A.N.N. news processing pipeline.
    
    Pipeline stages:
    1. Fact Extraction (legal compliance)
    2. Script Writing (original content creation)
    3. Critic Review (quality assurance & rewrite)
    4. Headline Generation
    5. Translations
    6. Audio Generation
    7. Video Generation
    """

    def __init__(self):
        self.fact_extractor = FactExtractorAgent()
        self.scriptwriter = ScriptwriterAgent()
        self.critic = CriticAgent()
        self.translator = TranslatorAgent()
        self.headline_gen = HeadlineGeneratorAgent()
        self.tts = ElevenLabsTTS()
        self.video_gen = HeyGenVideoGenerator()

    async def process_single_article(
        self,
        article: ArticleInput,
    ) -> BroadcastScript:
        """
        Process a single article through the editorial pipeline.
        """
        log.info(
            "processing_article",
            source=article.source_name,
            url=article.source_url,
            category=article.category.value,
        )

        # Step 1: Extract raw facts
        facts = await self.fact_extractor.extract(
            raw_text=article.raw_text,
            source_name=article.source_name,
        )

        # Step 2: Write the English broadcast script
        english_script = await self.scriptwriter.write(
            facts=facts,
            category=article.category.value,
        )

        # Step 2.5: Critic Review Loop for Best-in-Class Quality
        is_approved, feedback = await self.critic.review(facts, english_script)
        if not is_approved:
            log.info("script_rejected_by_critic", feedback=feedback[:100])
            # Force rewrite based on feedback
            english_script = await self.scriptwriter.write(
                facts=facts,
                category=article.category.value,
                previous_draft=english_script,
                feedback=feedback,
            )
        else:
            log.info("script_passed_critic_review")

        # Step 3 & 4: Generate headline and translate concurrently
        headline_task = self.headline_gen.generate(english_script)
        target_languages = ["Hindi", "Spanish", "Mandarin", "French", "Arabic"]
        translate_task = self.translator.translate(english_script, target_languages=target_languages)

        headline, translations = await asyncio.gather(headline_task, translate_task)

        # Build the final broadcast script
        script = BroadcastScript(
            headline=headline,
            english_script=english_script,
            hindi_script=translations.get("Hindi", ""),
            translations=translations,
            category=article.category,
            source_url=article.source_url,
        )

        from services.supabase_client import supabase_sync
        await supabase_sync.sync_script(script)

        log.info(
            "article_processed",
            script_id=script.id,
            headline=script.headline,
            duration_sec=script.estimated_duration_seconds,
        )

        return script

    async def run_full_pipeline(
        self,
        articles: list[ArticleInput],
        generate_media: bool = False,
        job: PipelineJob | None = None,
    ) -> PipelineJob:
        """
        Run the complete pipeline on a batch of articles.
        
        Args:
            articles: List of raw articles to process.
            generate_media: Whether to generate audio/video (costs $).
            job: Existing pipeline job to update, or creates a new one.
        """
        if job is None:
            job = await queue_manager.create_job()

        total_steps = len(articles)
        if generate_media:
            total_steps *= 3  # editorial + audio + video

        try:
            # ── Phase 1: Editorial Processing ──────────────────
            await queue_manager.update_job(
                job.job_id,
                status=PipelineStatus.EXTRACTING_FACTS,
                progress_pct=5,
            )

            scripts = []
            for i, article in enumerate(articles):
                try:
                    script = await self.process_single_article(article)
                    scripts.append(script)
                    
                    progress = int(((i + 1) / len(articles)) * 50)
                    await queue_manager.update_job(
                        job.job_id,
                        progress_pct=progress,
                    )
                except Exception as e:
                    log.error(
                        "article_processing_failed",
                        url=article.source_url,
                        error=str(e),
                    )
                    await queue_manager.update_job(
                        job.job_id,
                        error=f"Failed to process {article.source_url}: {str(e)}",
                    )

            job.scripts = scripts

            if not generate_media:
                await queue_manager.update_job(
                    job.job_id,
                    status=PipelineStatus.COMPLETED,
                    progress_pct=100,
                )
                log.info(
                    "pipeline_complete_editorial_only",
                    job_id=job.job_id,
                    scripts_generated=len(scripts),
                )
                return job

            # ── Phase 2: Audio Generation ──────────────────────
            await queue_manager.update_job(
                job.job_id,
                status=PipelineStatus.GENERATING_AUDIO,
                progress_pct=55,
            )

            for script in scripts:
                try:
                    # Generate English and Hindi audio concurrently
                    en_audio_task = self.tts.generate_audio(
                        script_id=script.id,
                        text=script.english_script,
                        language=Language.ENGLISH,
                    )
                    hi_audio_task = self.tts.generate_audio(
                        script_id=script.id,
                        text=script.hindi_script,
                        language=Language.HINDI,
                    )

                    en_audio, hi_audio = await asyncio.gather(
                        en_audio_task, hi_audio_task
                    )
                    job.audio_results.extend([en_audio, hi_audio])

                except Exception as e:
                    log.error("audio_generation_failed", script_id=script.id, error=str(e))
                    await queue_manager.update_job(
                        job.job_id,
                        error=f"Audio failed for {script.id}: {str(e)}",
                    )

            await queue_manager.update_job(job.job_id, progress_pct=75)

            # ── Phase 3: Video Generation ──────────────────────
            await queue_manager.update_job(
                job.job_id,
                status=PipelineStatus.GENERATING_VIDEO,
                progress_pct=80,
            )

            for script in scripts:
                try:
                    en_video = await self.video_gen.generate_video(
                        script_id=script.id,
                        script_text=script.english_script,
                        language=Language.ENGLISH,
                    )
                    job.video_results.append(en_video)
                except Exception as e:
                    log.error("video_generation_failed", script_id=script.id, error=str(e))
                    await queue_manager.update_job(
                        job.job_id,
                        error=f"Video failed for {script.id}: {str(e)}",
                    )

            # ── Pipeline Complete ──────────────────────────────
            final_status = (
                PipelineStatus.COMPLETED
                if not job.errors
                else PipelineStatus.COMPLETED  # Partial success is still "completed"
            )

            await queue_manager.update_job(
                job.job_id,
                status=final_status,
                progress_pct=100,
            )

            log.info(
                "pipeline_complete",
                job_id=job.job_id,
                scripts=len(scripts),
                audio_files=len(job.audio_results),
                video_files=len(job.video_results),
                errors=len(job.errors),
            )

            # Wait for any background tasks (like downloading media) to finish
            await asyncio.sleep(1)

            # --- Dispatch Automated Webhooks to B2B Clients ---
            from services.webhook import dispatch_webhooks
            import asyncio
            asyncio.create_task(dispatch_webhooks(job))
            log.info("webhook_dispatch_queued", job_id=job.job_id)

        except Exception as e:
            log.error("pipeline_fatal_error", job_id=job.job_id, error=str(e))
            await queue_manager.update_job(
                job.job_id,
                status=PipelineStatus.FAILED,
                error=f"Fatal: {str(e)}",
            )

        return job
