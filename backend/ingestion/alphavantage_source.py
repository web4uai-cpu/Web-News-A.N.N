"""
A.N.N. Alpha Vantage Source
Fetches real-time financial and stock market data.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ingestion.base_source import BaseNewsSource
from models.schemas import ArticleInput, NewsCategory
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("alphavantage_source")


class AlphaVantageSource(BaseNewsSource):
    """Fetches financial news and market data from Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.alpha_vantage_key

    @property
    def source_name(self) -> str:
        return "Alpha Vantage"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
    )
    async def fetch_articles(
        self,
        category: str = "finance",
        query: str | None = None,
        max_articles: int = 5,
    ) -> list[ArticleInput]:
        """Fetch financial news from Alpha Vantage News Sentiment API."""
        await rate_limiter.acquire("newsapi")  # Shares newsapi rate limit bucket

        if not self.api_key:
            log.warning("alphavantage_key_missing", msg="ALPHA_VANTAGE_KEY not set")
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": self.api_key,
                "limit": max_articles,
                "sort": "LATEST",
            }

            if query:
                params["tickers"] = query  # Alpha Vantage uses ticker symbols

            log.info("fetching_alphavantage", tickers=query)

            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        feed = data.get("feed", [])

        for item in feed[:max_articles]:
            title = item.get("title", "")
            summary = item.get("summary", "")
            source = item.get("source", "Alpha Vantage")
            published = item.get("time_published", "")

            # Build ticker context
            tickers = item.get("ticker_sentiment", [])
            ticker_info = ""
            if tickers:
                ticker_lines = []
                for t in tickers[:5]:
                    ticker_lines.append(
                        f"  - {t.get('ticker', 'N/A')}: "
                        f"Sentiment={t.get('ticker_sentiment_label', 'N/A')}, "
                        f"Score={t.get('ticker_sentiment_score', 'N/A')}"
                    )
                ticker_info = "\nTicker Sentiment:\n" + "\n".join(ticker_lines)

            # Overall sentiment
            overall_sentiment = item.get("overall_sentiment_label", "Neutral")
            sentiment_score = item.get("overall_sentiment_score", "N/A")

            full_text = (
                f"Title: {title}\n\n"
                f"Summary: {summary}\n\n"
                f"Published: {published}\n"
                f"Source: {source}\n"
                f"Overall Sentiment: {overall_sentiment} (Score: {sentiment_score})"
                f"{ticker_info}"
            )

            if len(full_text) >= 50:
                articles.append(
                    ArticleInput(
                        source_url=item.get("url", ""),
                        raw_text=full_text,
                        source_name=source,
                        category=NewsCategory.FINANCE,
                    )
                )

        log.info("alphavantage_fetched", article_count=len(articles))
        return articles

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
    )
    async def fetch_stock_quote(self, symbol: str) -> dict:
        """Fetch a real-time stock quote for additional context."""
        if not self.api_key:
            return {}

        async with httpx.AsyncClient(timeout=15.0) as client:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key,
            }
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        quote = data.get("Global Quote", {})
        return {
            "symbol": quote.get("01. symbol", symbol),
            "price": quote.get("05. price", "N/A"),
            "change": quote.get("09. change", "N/A"),
            "change_pct": quote.get("10. change percent", "N/A"),
            "volume": quote.get("06. volume", "N/A"),
        }
