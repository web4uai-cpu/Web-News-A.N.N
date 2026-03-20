"""
A.N.N. Critic Agent
Agent Review Loop: Acts as a senior executive editor to review drafted scripts 
for factual accuracy, bias, and engagement. Forces rewrites if standards are not met.
"""

from typing import Tuple
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("critic")

CRITIC_SYSTEM_PROMPT = """You are the Senior Executive Producer of the world's leading news network.
Your job is to mercilessly review broadcast news scripts submitted by your junior writers.

QUALITY STANDARDS:
1. Pacing & Hooks: Does the opening sentence instantly grab attention?
2. Objectivity: Is there any hidden bias or sensationalism?
3. Clarity: Are there any clunky sentences that an anchor would stumble over?
4. Conciseness: Can it be said with fewer, more powerful words?

INSTRUCTIONS:
You will be provided with the Source Facts and the Drafted Script.
Review the draft against the Source Facts. If the script hallucinates any details NOT in the facts, it FAILS.

OUTPUT FORMAT:
First line MUST be either "PASS" or "REJECT".
If "REJECT", provide a 1-3 sentence explanation of exactly what to fix.
If "PASS", output a 1 sentence compliment.
"""


class CriticAgent:
    """Reviews broadcast scripts for premium quality assurance."""

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
    async def review(self, facts: str, draft_script: str) -> Tuple[bool, str]:
        """
        Review a drafted script.
        
        Returns:
            (is_approved: bool, feedback: str)
        """
        await rate_limiter.acquire("llm")

        log.info("reviewing_draft_script")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"SOURCE FACTS:\n{facts}\n\nDRAFT SCRIPT:\n{draft_script}",
                },
            ],
            temperature=0.1,  # Strict, analytical temperature
            max_tokens=300,
        )

        review_text = response.choices[0].message.content.strip()
        is_approved = review_text.upper().startswith("PASS")
        
        log.info("script_review_completed", approved=is_approved, feedback=review_text[:100])

        return is_approved, review_text
