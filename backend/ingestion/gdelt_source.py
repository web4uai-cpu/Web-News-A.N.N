"""
A.N.N. GDELT Source
Fetches geopolitical event data from the GDELT Project (Free/Open Source).
Uses the GDELT DOC 2.0 API for article search.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ingestion.base_source import BaseNewsSource
from models.schemas import ArticleInput, NewsCategory
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger

log = get_logger("gdelt_source")

# GDELT theme codes to internal categories
THEME_MAP = {
    "POLITICS": NewsCategory.POLITICS,
    "ECON": NewsCategory.FINANCE,
    "MILITARY": NewsCategory.GEOPOLITICS,
    "HEALTH": NewsCategory.HEALTH,
    "SCIENCE": NewsCategory.SCIENCE,
    "TECHNOLOGY": NewsCategory.TECHNOLOGY,
    "SPORTS": NewsCategory.SPORTS,
}


class GDELTSource(BaseNewsSource):
    """
    Fetches geopolitical events from the GDELT Project.
    Uses the GDELT DOC 2.0 API (free, no API key required).
    """

    DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self):
        pass  # GDELT is free — no API key needed

    @property
    def source_name(self) -> str:
        return "GDELT Project"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
    )
    async def fetch_articles(
        self,
        category: str = "geopolitics",
        query: str | None = None,
        max_articles: int = 5,
    ) -> list[ArticleInput]:
        """
        Fetch articles from GDELT DOC 2.0 API.
        
        GDELT provides global event monitoring without requiring an API key.
        """
        await rate_limiter.acquire("newsapi")

        search_query = query or self._category_to_query(category)

        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": search_query,
                "mode": "ArtList",
                "maxrecords": str(max_articles),
                "format": "json",
                "sort": "DateDesc",
                "sourcelang": "eng",
            }

            log.info("fetching_gdelt", query=search_query, max_articles=max_articles)

            response = await client.get(self.DOC_API_URL, params=params)
            response.raise_for_status()
            
            # GDELT may return empty results
            try:
                data = response.json()
            except Exception:
                log.warning("gdelt_empty_response")
                return []

        articles = []
        items = data.get("articles", [])

        for item in items[:max_articles]:
            title = item.get("title", "")
            url = item.get("url", "")
            source_name = item.get("domain", "GDELT")
            seendate = item.get("seendate", "")
            language = item.get("language", "English")
            source_country = item.get("sourcecountry", "Unknown")

            # Build contextual text from GDELT metadata
            full_text = (
                f"Title: {title}\n\n"
                f"Source: {source_name}\n"
                f"Country: {source_country}\n"
                f"Language: {language}\n"
                f"Date: {seendate}\n\n"
                f"This article was detected by the GDELT global event monitoring system "
                f"and relates to: {search_query}."
            )

            # GDELT articles are metadata-heavy; we may need to separately
            # scrape the actual article content in a production system.
            # For MVP, we use the title + metadata.
            if len(full_text) >= 50:
                mapped_category = self._map_category(category)
                articles.append(
                    ArticleInput(
                        source_url=url,
                        raw_text=full_text,
                        source_name=source_name,
                        category=mapped_category,
                    )
                )

        log.info("gdelt_fetched", article_count=len(articles))
        return articles

    @staticmethod
    def _category_to_query(category: str) -> str:
        """Convert internal category to GDELT search query."""
        query_map = {
            "geopolitics": "geopolitics conflict diplomacy",
            "politics": "government politics election",
            "finance": "economy markets trade",
            "technology": "technology innovation AI",
            "health": "health pandemic WHO",
            "science": "science research discovery",
            "general": "world news breaking",
        }
        return query_map.get(category, "world news")

    @staticmethod
    def _map_category(category: str) -> NewsCategory:
        """Map string category to NewsCategory enum."""
        try:
            return NewsCategory(category)
        except ValueError:
            return NewsCategory.GEOPOLITICS
