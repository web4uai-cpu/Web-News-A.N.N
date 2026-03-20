"""
A.N.N. Fact Extractor Agent
Agent 1: Strips copyright material, leaving only verifiable raw facts.
This is the critical legal compliance layer.
"""

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("fact_extractor")

FACT_EXTRACTOR_SYSTEM_PROMPT = """You are a Legal Compliance AI and Senior Intelligence Analyst.

YOUR MISSION:
Read the following copyrighted news article and extract ONLY the verified, indisputable facts.

RULES — FOLLOW STRICTLY:
1. Extract ONLY: names, dates, numbers, locations, official statements, and verifiable events.
2. STRIP AWAY: all original journalistic prose, opinions, analysis, metaphors, and creative formatting.
3. DO NOT copy any sentence structure from the original article.
4. DO NOT include the journalist's interpretation or speculation.
5. Present facts as a clean bulleted list.
6. Each bullet should be a single, atomic fact.
7. Include the source attribution only as "Source: [publication name]" at the end.

OUTPUT FORMAT:
• [Fact 1]
• [Fact 2]
• [Fact 3]
...
Source: [Publication Name]
"""


class FactExtractorAgent:
    """Extracts raw facts from copyrighted news articles for legal compliance."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_model

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=15, max=60),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: get_logger("fact_extractor").warning(
            "retry_attempt",
            attempt=retry_state.attempt_number,
            error=str(retry_state.outcome.exception()) if retry_state.outcome else "unknown",
        ),
    )
    async def extract(self, raw_text: str, source_name: str = "Unknown") -> str:
        """
        Extract facts from raw article text.
        
        Args:
            raw_text: The full copyrighted article text.
            source_name: Name of the source publication.
            
        Returns:
            A bulleted list of raw facts.
        """
        await rate_limiter.acquire("llm")

        log.info("extracting_facts", source=source_name, text_length=len(raw_text))

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": FACT_EXTRACTOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Source: {source_name}\n\nArticle:\n{raw_text}",
                },
            ],
            temperature=0.0,  # Zero creativity — pure fact extraction
            max_tokens=2000,
        )

        facts = response.choices[0].message.content
        fact_lines = [l for l in facts.strip().split("\n") if l.strip().startswith("•")]
        
        log.info(
            "facts_extracted",
            source=source_name,
            fact_count=len(fact_lines),
        )

        return facts
