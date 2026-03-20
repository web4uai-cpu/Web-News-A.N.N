"""
A.N.N. Facebook Page Auto-Poster
Posts generated news to a Facebook Page using the Graph API.
"""

import httpx
from utils.logger import get_logger
from config import get_settings

log = get_logger("social.facebook")


class FacebookPoster:
    """Post news to a Facebook Page."""

    GRAPH_API = "https://graph.facebook.com/v19.0"

    def __init__(self):
        settings = get_settings()
        self.page_token = settings.facebook_page_token
        self.page_id = settings.facebook_page_id
        self.enabled = bool(self.page_token and self.page_id)

    async def post_to_page(
        self,
        headline: str,
        excerpt: str = "",
        category: str = "",
        news_url: str = "",
    ) -> dict:
        """
        Post a link + message to the configured Facebook Page.

        Args:
            headline: News headline.
            excerpt: Script excerpt for the post body.
            category: Category for context.
            news_url: Link to the full story.

        Returns:
            Facebook API response or error dict.
        """
        if not self.enabled:
            log.warning("facebook_disabled", reason="No FB credentials configured")
            return {"status": "skipped", "reason": "Facebook not configured"}

        # Build post message
        message = f"🔴 {headline}\n\n"
        if excerpt:
            trim_excerpt = excerpt[:400] + "..." if len(excerpt) > 400 else excerpt
            message += f"{trim_excerpt}\n\n"
        message += f"📺 #{category.title().replace(' ', '')} #ANN #AINewsNetwork"

        payload = {
            "message": message,
            "access_token": self.page_token,
        }
        if news_url:
            payload["link"] = news_url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.GRAPH_API}/{self.page_id}/feed",
                    data=payload,
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    post_id = data.get("id", "")
                    log.info("facebook_posted", post_id=post_id)
                    return {
                        "status": "posted",
                        "platform": "facebook",
                        "post_id": post_id,
                    }
                else:
                    log.error(
                        "facebook_failed",
                        status=response.status_code,
                        body=response.text[:200],
                    )
                    return {
                        "status": "failed",
                        "platform": "facebook",
                        "error": response.text[:200],
                    }

        except Exception as e:
            log.error("facebook_exception", error=str(e))
            return {"status": "error", "platform": "facebook", "error": str(e)}
