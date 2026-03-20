"""
A.N.N. Headline Generator Agent
Agent 4: Creates attention-grabbing headlines from broadcast scripts.
"""

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("headline_generator")

HEADLINE_SYSTEM_PROMPT = """You are a veteran news headline writer for a top-tier international news network.

YOUR MISSION:
Create a single compelling, attention-grabbing headline for the given news script.

RULES:
1. Maximum 12 words.
2. Use active voice.
3. Be specific — include the key who/what.
4. Create urgency without clickbait.
5. No quotation marks unless quoting someone.
6. Capitalize as per AP Style (Title Case).

OUTPUT: Only the headline text, nothing else.
"""


class HeadlineGeneratorAgent:
    """Generates broadcast-quality headlines."""

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
    )
    async def generate(self, script: str) -> str:
        """Generate a headline for a broadcast script."""
        await rate_limiter.acquire("llm")

        log.info("generating_headline")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": HEADLINE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Script:\n{script}"},
            ],
            temperature=0.8,
            max_tokens=50,
        )

        headline = response.choices[0].message.content.strip().strip('"')

        log.info("headline_generated", headline=headline)
        return headline
