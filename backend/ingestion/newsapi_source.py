"""
A.N.N. NewsAPI Source
Fetches global headlines and articles from NewsAPI.org.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ingestion.base_source import BaseNewsSource
from models.schemas import ArticleInput, NewsCategory
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("newsapi_source")

# Map internal categories to NewsAPI categories
CATEGORY_MAP = {
    NewsCategory.GENERAL: "general",
    NewsCategory.BUSINESS: "business",
    NewsCategory.TECHNOLOGY: "technology",
    NewsCategory.SCIENCE: "science",
    NewsCategory.HEALTH: "health",
    NewsCategory.SPORTS: "sports",
    NewsCategory.ENTERTAINMENT: "entertainment",
    NewsCategory.POLITICS: "general",
    NewsCategory.FINANCE: "business",
    NewsCategory.GEOPOLITICS: "general",
}


class NewsAPISource(BaseNewsSource):
    """Fetches articles from NewsAPI.org."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.news_api_key

    @property
    def source_name(self) -> str:
        return "NewsAPI"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
    )
    async def fetch_articles(
        self,
        category: str = "general",
        query: str | None = None,
        max_articles: int = 5,
    ) -> list[ArticleInput]:
        """Fetch top headlines or search articles from NewsAPI."""
        await rate_limiter.acquire("newsapi")

        if not self.api_key:
            log.warning("newsapi_key_missing", msg="NEWS_API_KEY not set, returning empty")
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if query:
                # Use /everything endpoint for search
                url = f"{self.BASE_URL}/everything"
                params = {
                    "q": query,
                    "sortBy": "publishedAt",
                    "pageSize": max_articles,
                    "apiKey": self.api_key,
                    "language": "en",
                }
            else:
                # Use /top-headlines for category browsing
                url = f"{self.BASE_URL}/top-headlines"
                api_category = CATEGORY_MAP.get(
                    NewsCategory(category) if category in [e.value for e in NewsCategory] else NewsCategory.GENERAL,
                    "general",
                )
                params = {
                    "category": api_category,
                    "pageSize": max_articles,
                    "apiKey": self.api_key,
                    "language": "en",
                    "country": "us",
                }

            log.info("fetching_newsapi", url=url, params={k: v for k, v in params.items() if k != "apiKey"})

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        for item in data.get("articles", [])[:max_articles]:
            # Skip articles with [Removed] content
            content = item.get("content") or item.get("description") or ""
            if not content or "[Removed]" in content or len(content) < 50:
                continue

            # Combine title, description, and content for maximum fact extraction
            full_text = "\n\n".join(
                filter(None, [
                    f"Title: {item.get('title', '')}",
                    f"Description: {item.get('description', '')}",
                    f"Content: {content}",
                    f"Published: {item.get('publishedAt', '')}",
                ])
            )

            articles.append(
                ArticleInput(
                    source_url=item.get("url", ""),
                    raw_text=full_text,
                    source_name=item.get("source", {}).get("name", "NewsAPI"),
                    category=NewsCategory(category) if category in [e.value for e in NewsCategory] else NewsCategory.GENERAL,
                )
            )

        log.info("newsapi_fetched", article_count=len(articles))
        return articles
