"""
A.N.N. Research Writer Agent
Generates long-form 5,000+ word research reports from multi-article deep analysis.
"""

from datetime import datetime, timezone
from uuid import uuid4

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("research_writer")

REPORT_SYSTEM_PROMPT = """You are a senior research analyst at A.N.N. (AI News Network).
Write a comprehensive, authoritative research report on the given topic.

Requirements:
- 5,000+ words with clear structure
- Executive Summary (200 words)
- Key Findings (bullet points)
- Detailed Analysis (multiple sections)
- Data & Statistics (reference provided sources)
- Risk Assessment
- Outlook & Predictions
- Methodology note

Style: Professional, data-driven, objective. Avoid speculation without evidence.
Format: Markdown with headers, tables, and bullet points."""


class ResearchReport:
    def __init__(
        self,
        id: str = "",
        topic: str = "",
        status: str = "pending",
    ):
        self.id = id or str(uuid4())
        self.topic = topic
        self.status = status
        self.sources: list[dict] = []
        self.content: str = ""
        self.word_count: int = 0
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.completed_at: str | None = None


class ResearchWriterAgent:
    def __init__(self):
        self.settings = get_settings()

    async def gather_sources(self, topic: str, max_articles: int = 50) -> list[dict]:
        log.info("gathering_sources", topic=topic, max_articles=max_articles)
        return [
            {"title": f"Source article about {topic}", "source": "aggregated", "relevance": 0.9}
        ]

    async def generate_report(self, topic: str, sources: list[dict]) -> ResearchReport:
        report = ResearchReport(topic=topic, status="generating")

        await rate_limiter.acquire("llm")

        source_context = "\n".join(
            f"- {s.get('title', 'Unknown')} (Source: {s.get('source', 'N/A')})"
            for s in sources[:50]
        )

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Topic: {topic}\n\nSources:\n{source_context}\n\nWrite the full research report."},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 16384,
                },
            )
            response.raise_for_status()
            data = response.json()

        report.content = data["choices"][0]["message"]["content"]
        report.word_count = len(report.content.split())
        report.sources = sources
        report.status = "completed"
        report.completed_at = datetime.now(timezone.utc).isoformat()

        log.info("report_generated", topic=topic, word_count=report.word_count)
        return report


class SentimentAgent:
    def __init__(self):
        self.settings = get_settings()

    async def analyze_sentiment(self, text: str, entity: str = "") -> dict:
        await rate_limiter.acquire("llm")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": "Analyze the sentiment of this news text. Return JSON: {\"sentiment\": \"positive|negative|neutral\", \"score\": -1.0 to 1.0, \"confidence\": 0 to 1, \"key_factors\": []}"},
                        {"role": "user", "content": f"Entity: {entity}\n\nText: {text}"},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "entity": entity,
            "analysis": data["choices"][0]["message"]["content"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def score_market_impact(self, headline: str) -> dict:
        await rate_limiter.acquire("llm")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": "Rate the market impact of this news headline on a scale of 1-10. Return JSON: {\"impact_score\": int, \"affected_sectors\": [], \"reasoning\": str}"},
                        {"role": "user", "content": headline},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "headline": headline,
            "analysis": data["choices"][0]["message"]["content"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
