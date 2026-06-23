"""
A.N.N. Platform Upload Service
Handles uploading short-form videos to YouTube Shorts, Instagram Reels, and TikTok.
"""

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("platform_upload")


class PlatformUploader:
    def __init__(self):
        self.settings = get_settings()

    async def upload_youtube_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
    ) -> dict:
        log.info("uploading_youtube_short", title=title)
        return {
            "platform": "youtube_shorts",
            "status": "pending_oauth",
            "message": "YouTube Shorts upload requires OAuth2 flow — use youtube.py service",
            "video_path": video_path,
            "title": title,
        }

    async def upload_instagram_reel(
        self,
        video_path: str,
        caption: str,
    ) -> dict:
        if not self.settings.instagram_access_token:
            return {"platform": "instagram_reels", "status": "skipped", "reason": "no_token"}

        await rate_limiter.acquire("instagram")

        async with httpx.AsyncClient(timeout=120.0) as client:
            create_resp = await client.post(
                f"https://graph.facebook.com/v18.0/{self.settings.instagram_account_id}/media",
                params={
                    "media_type": "REELS",
                    "video_url": video_path,
                    "caption": caption,
                    "access_token": self.settings.instagram_access_token,
                },
            )
            create_resp.raise_for_status()
            container_id = create_resp.json()["id"]

            publish_resp = await client.post(
                f"https://graph.facebook.com/v18.0/{self.settings.instagram_account_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": self.settings.instagram_access_token,
                },
            )
            publish_resp.raise_for_status()

        log.info("instagram_reel_published", container_id=container_id)
        return {
            "platform": "instagram_reels",
            "status": "published",
            "media_id": publish_resp.json().get("id"),
        }

    async def upload_tiktok(
        self,
        video_path: str,
        caption: str,
    ) -> dict:
        log.info("tiktok_upload_placeholder", caption=caption[:50])
        return {
            "platform": "tiktok",
            "status": "pending_integration",
            "message": "TikTok Content Posting API requires app review and approval",
            "video_path": video_path,
        }

    async def upload_all(
        self,
        variants: dict[str, str],
        title: str,
        description: str,
        tags: list[str] | None = None,
    ) -> dict[str, dict]:
        results = {}

        if "youtube_shorts" in variants:
            results["youtube_shorts"] = await self.upload_youtube_short(
                variants["youtube_shorts"], title, description, tags
            )

        if "instagram_reels" in variants:
            results["instagram_reels"] = await self.upload_instagram_reel(
                variants["instagram_reels"], f"{title}\n\n{description}"
            )

        if "tiktok" in variants:
            results["tiktok"] = await self.upload_tiktok(
                variants["tiktok"], f"{title} {description}"
            )

        return results
