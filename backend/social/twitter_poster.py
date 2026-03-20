"""
A.N.N. Twitter/X Auto-Poster
Posts generated news headlines to Twitter/X using the v2 API.
Free Basic tier: 1,500 posts/month.
"""

import httpx
from utils.logger import get_logger
from config import get_settings

log = get_logger("social.twitter")


class TwitterPoster:
    """Post news headlines and links to Twitter/X."""

    API_URL = "https://api.twitter.com/2/tweets"

    def __init__(self):
        settings = get_settings()
        self.bearer_token = settings.twitter_bearer_token
        self.enabled = bool(self.bearer_token)

    async def post_tweet(
        self,
        headline: str,
        category: str = "",
        script_id: str = "",
        news_url: str = "",
    ) -> dict:
        """
        Post a tweet with the news headline.

        Args:
            headline: The news headline to tweet.
            category: News category for hashtag.
            script_id: Script ID for linking.
            news_url: Public URL to the news page.

        Returns:
            Twitter API response or error dict.
        """
        if not self.enabled:
            log.warning("twitter_disabled", reason="No TWITTER_BEARER_TOKEN configured")
            return {"status": "skipped", "reason": "Twitter not configured"}

        # Build tweet text
        hashtag = f"#{category.title().replace(' ', '')}" if category else "#News"
        link = news_url or f"https://yoursite.com/news#script-{script_id}"

        tweet_text = f"🔴 BREAKING | {headline}\n\n{hashtag} #ANN #AINews\n{link}"

        # Trim to 280 chars
        if len(tweet_text) > 280:
            max_headline_len = 280 - len(f"🔴 BREAKING | \n\n{hashtag} #ANN #AINews\n{link}")
            headline_trimmed = headline[:max_headline_len - 3] + "..."
            tweet_text = f"🔴 BREAKING | {headline_trimmed}\n\n{hashtag} #ANN #AINews\n{link}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.bearer_token}",
                        "Content-Type": "application/json",
                    },
                    json={"text": tweet_text},
                    timeout=15.0,
                )

                if response.status_code == 201:
                    data = response.json()
                    tweet_id = data.get("data", {}).get("id", "")
                    log.info(
                        "tweet_posted",
                        tweet_id=tweet_id,
                        headline=headline[:50],
                    )
                    return {
                        "status": "posted",
                        "platform": "twitter",
                        "tweet_id": tweet_id,
                        "url": f"https://twitter.com/i/web/status/{tweet_id}",
                    }
                else:
                    log.error(
                        "tweet_failed",
                        status=response.status_code,
                        body=response.text[:200],
                    )
                    return {
                        "status": "failed",
                        "platform": "twitter",
                        "error": response.text[:200],
                    }

        except Exception as e:
            log.error("tweet_exception", error=str(e))
            return {"status": "error", "platform": "twitter", "error": str(e)}
