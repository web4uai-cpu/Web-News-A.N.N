"""
A.N.N. Social Media Scheduler
Automatically posts to all configured social platforms when a new script is generated.
"""

import asyncio
from models.schemas import BroadcastScript
from social.twitter_poster import TwitterPoster
from social.facebook_poster import FacebookPoster
from social.instagram_poster import InstagramPoster
from utils.logger import get_logger

log = get_logger("social.scheduler")


class SocialScheduler:
    """
    Orchestrates auto-posting to all social media platforms.
    
    Call `broadcast()` after each script is generated in the pipeline
    to automatically distribute to Twitter, Facebook, and Instagram.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.twitter = TwitterPoster()
        self.facebook = FacebookPoster()
        self.instagram = InstagramPoster()
        self.base_url = base_url
        self.enabled_platforms: list[str] = []

        if self.twitter.enabled:
            self.enabled_platforms.append("twitter")
        if self.facebook.enabled:
            self.enabled_platforms.append("facebook")
        if self.instagram.enabled:
            self.enabled_platforms.append("instagram")

        log.info(
            "social_scheduler_ready",
            platforms=self.enabled_platforms or ["none"],
        )

    @property
    def is_any_enabled(self) -> bool:
        return len(self.enabled_platforms) > 0

    async def broadcast(self, script: BroadcastScript) -> dict:
        """
        Broadcast a script to all configured social media platforms.

        Args:
            script: The broadcast script to share.

        Returns:
            Dict with results from each platform.
        """
        if not self.is_any_enabled:
            log.debug("social_broadcast_skip", reason="No platforms configured")
            return {"status": "skipped", "reason": "No social platforms configured"}

        news_url = f"{self.base_url}/news#script-{script.id}"
        excerpt = script.english_script.replace("[PAUSE]", "").strip()[:400]

        results = {}

        # Run all posts concurrently
        tasks = []

        if self.twitter.enabled:
            tasks.append(("twitter", self.twitter.post_tweet(
                headline=script.headline,
                category=script.category.value,
                script_id=script.id,
                news_url=news_url,
            )))

        if self.facebook.enabled:
            tasks.append(("facebook", self.facebook.post_to_page(
                headline=script.headline,
                excerpt=excerpt,
                category=script.category.value,
                news_url=news_url,
            )))

        if self.instagram.enabled:
            tasks.append(("instagram", self.instagram.post_to_instagram(
                headline=script.headline,
                category=script.category.value,
                script_id=script.id,
            )))

        # Execute all concurrently
        for platform, coro in tasks:
            try:
                result = await coro
                results[platform] = result
                log.info(
                    "social_posted",
                    platform=platform,
                    status=result.get("status"),
                    headline=script.headline[:40],
                )
            except Exception as e:
                results[platform] = {"status": "error", "error": str(e)}
                log.error("social_broadcast_error", platform=platform, error=str(e))

        return {
            "status": "broadcast_complete",
            "platforms": results,
            "headline": script.headline,
        }

    async def broadcast_batch(self, scripts: list[BroadcastScript]) -> list[dict]:
        """
        Broadcast multiple scripts with a delay between each to avoid rate limits.
        """
        results = []
        for i, script in enumerate(scripts):
            result = await self.broadcast(script)
            results.append(result)
            if i < len(scripts) - 1:
                await asyncio.sleep(2)  # 2s gap between posts
        return results
