"""
Social media posting — Twitter, Facebook, Instagram.
Extracted from monolith social/ directory.
"""

import httpx
from config import get_settings


async def post_twitter(headline: str, category: str, news_url: str) -> dict:
    settings = get_settings()
    if not settings.twitter_bearer_token:
        return {"status": "skipped", "platform": "twitter", "reason": "Not configured"}

    hashtag = f"#{category.title().replace(' ', '')}" if category else "#News"
    tweet = f"🔴 BREAKING | {headline}\n\n{hashtag} #ANN #AINews\n{news_url}"
    if len(tweet) > 280:
        max_hl = 280 - len(f"🔴 BREAKING | \n\n{hashtag} #ANN #AINews\n{news_url}")
        tweet = f"🔴 BREAKING | {headline[:max_hl-3]}...\n\n{hashtag} #ANN #AINews\n{news_url}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.twitter.com/2/tweets",
                headers={"Authorization": f"Bearer {settings.twitter_bearer_token}", "Content-Type": "application/json"},
                json={"text": tweet},
            )
            if r.status_code == 201:
                tid = r.json().get("data", {}).get("id", "")
                return {"status": "posted", "platform": "twitter", "tweet_id": tid}
            return {"status": "failed", "platform": "twitter", "error": r.text[:200]}
    except Exception as e:
        return {"status": "error", "platform": "twitter", "error": str(e)}


async def post_facebook(headline: str, excerpt: str, category: str, news_url: str) -> dict:
    settings = get_settings()
    if not settings.facebook_page_token or not settings.facebook_page_id:
        return {"status": "skipped", "platform": "facebook", "reason": "Not configured"}

    message = f"📰 {headline}\n\n{excerpt[:300]}\n\n🔗 Read more: {news_url}\n\n#ANN #AINews #{category.title()}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"https://graph.facebook.com/v19.0/{settings.facebook_page_id}/feed",
                data={"message": message, "link": news_url, "access_token": settings.facebook_page_token},
            )
            if r.status_code == 200:
                pid = r.json().get("id", "")
                return {"status": "posted", "platform": "facebook", "post_id": pid}
            return {"status": "failed", "platform": "facebook", "error": r.text[:200]}
    except Exception as e:
        return {"status": "error", "platform": "facebook", "error": str(e)}


async def post_instagram(headline: str, category: str, image_url: str) -> dict:
    settings = get_settings()
    if not settings.instagram_access_token or not settings.instagram_account_id:
        return {"status": "skipped", "platform": "instagram", "reason": "Not configured"}

    caption = f"📺 {headline}\n\n#ANN #AINews #{category.title()} #BreakingNews"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            create = await client.post(
                f"https://graph.facebook.com/v19.0/{settings.instagram_account_id}/media",
                data={"image_url": image_url, "caption": caption, "access_token": settings.instagram_access_token},
            )
            media_id = create.json().get("id")
            if not media_id:
                return {"status": "failed", "platform": "instagram", "error": create.text[:200]}

            publish = await client.post(
                f"https://graph.facebook.com/v19.0/{settings.instagram_account_id}/media_publish",
                data={"creation_id": media_id, "access_token": settings.instagram_access_token},
            )
            if publish.status_code == 200:
                return {"status": "posted", "platform": "instagram", "media_id": publish.json().get("id", "")}
            return {"status": "failed", "platform": "instagram", "error": publish.text[:200]}
    except Exception as e:
        return {"status": "error", "platform": "instagram", "error": str(e)}


async def broadcast_all(headline: str, excerpt: str, category: str, script_id: str) -> dict:
    settings = get_settings()
    news_url = f"{settings.public_url}/news#script-{script_id}"
    results = {}

    for name, coro in [
        ("twitter", post_twitter(headline, category, news_url)),
        ("facebook", post_facebook(headline, excerpt, category, news_url)),
    ]:
        try:
            results[name] = await coro
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

    return {"status": "broadcast_complete", "platforms": results, "headline": headline}


def get_enabled_platforms() -> list[str]:
    s = get_settings()
    platforms = []
    if s.twitter_bearer_token:
        platforms.append("twitter")
    if s.facebook_page_token and s.facebook_page_id:
        platforms.append("facebook")
    if s.instagram_access_token and s.instagram_account_id:
        platforms.append("instagram")
    return platforms
