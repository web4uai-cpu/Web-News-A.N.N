"""
A.N.N. Base News Source
Abstract base class for all news ingestion sources.
"""

from abc import ABC, abstractmethod
from models.schemas import ArticleInput


class BaseNewsSource(ABC):
    """Abstract base for news data sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the source."""
        ...

    @abstractmethod
    async def fetch_articles(
        self,
        category: str = "general",
        query: str | None = None,
        max_articles: int = 5,
    ) -> list[ArticleInput]:
        """
        Fetch articles from the source.
        
        Args:
            category: News category to fetch.
            query: Optional search query.
            max_articles: Maximum number of articles to return.
            
        Returns:
            List of ArticleInput objects ready for processing.
        """
        ...
