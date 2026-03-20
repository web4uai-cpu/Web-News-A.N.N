"""
A.N.N. Scriptwriter Agent
Agent 2: Takes raw facts and writes an original, broadcast-ready news script.
"""

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("scriptwriter")

SCRIPTWRITER_SYSTEM_PROMPT = """You are an elite international news anchor and broadcast scriptwriter.

YOUR MISSION:
Take the raw facts provided and write a punchy, engaging broadcast script for a LIVE news segment.

STYLE GUIDELINES:
1. Write for SPOKEN delivery, not print. Use short, punchy sentences.
2. Open with a strong hook that grabs the viewer's attention.
3. Include natural pauses marked with [PAUSE] for dramatic effect.
4. Tone: Authoritative but accessible. Think BBC World Service meets Vice News.
5. Target duration: 30-60 seconds when read aloud (~75-150 words).
6. End with a concise sign-off or forward-looking statement.
7. DO NOT use bullet points — write in flowing broadcast prose.
8. DO NOT plagiarize — create entirely original prose from the facts.

STRUCTURE:
[ANCHOR INTRO] - 1-2 sentences, the hook.
[BODY] - 3-5 sentences expanding the story with key facts.
[CLOSING] - 1 sentence wrap-up or what to watch for next.

OUTPUT: Only the script text, ready to be read by the anchor. No stage directions 
except [PAUSE] markers.
"""


class ScriptwriterAgent:
    """Writes original broadcast scripts from extracted facts."""

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
    async def write(self, facts: str, category: str = "general", previous_draft: str = None, feedback: str = None) -> str:
        """
        Write a broadcast script from extracted facts.
        
        Args:
            facts: Bulleted list of extracted facts.
            category: News category for tone adjustment.
            previous_draft: Previous script if rewriting.
            feedback: Critic feedback to implement.
            
        Returns:
            A broadcast-ready script in English.
        """
        await rate_limiter.acquire("llm")

        user_content = f"Category: {category.upper()}\n\nRaw Facts:\n{facts}"
        
        if previous_draft and feedback:
            log.info("rewriting_script_from_feedback", category=category)
            user_content += f"\n\nPREVIOUS DRAFT:\n{previous_draft}\n\nCRITIC FEEDBACK MUST FIX:\n{feedback}"
        else:
            log.info("writing_script", category=category)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SCRIPTWRITER_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,  # Creative enough for engaging prose
            max_tokens=1000,
        )

        script = response.choices[0].message.content
        word_count = len(script.split())
        estimated_seconds = int((word_count / 150) * 60)

        log.info(
            "script_written",
            word_count=word_count,
            estimated_duration_sec=estimated_seconds,
            is_rewrite=bool(previous_draft),
        )

        return script
