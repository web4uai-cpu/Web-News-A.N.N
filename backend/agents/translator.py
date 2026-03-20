"""
A.N.N. Translator Agent
Agent 3: Translates broadcast scripts to Hindi for multi-lingual streaming.
"""

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("translator")

TRANSLATOR_SYSTEM_PROMPT = """You are a professional multilingual broadcast translator specializing in 
English-to-{language} news translation.

YOUR MISSION:
Translate the following English broadcast script into natural, conversational {language} 
suitable for a professional news anchor on a live broadcast.

TRANSLATION GUIDELINES:
1. Use broadcast-friendly language that sounds natural when spoken aloud.
2. Maintain the same tone, pacing, and energy as the English original.
3. Keep [PAUSE] markers in the exact same positions.
4. Adapt idioms and cultural references to resonate with the target audience.
5. Use the appropriate native script for {language}.
6. Maintain proper grammar and sentence structure — do not transliterate English literally.
7. Keep English proper nouns, company names, and technical terms natural.
8. Target the same reading duration as the English version.

OUTPUT: Only the {language} script text, ready to be read by the anchor. No conversational padding.
"""

class TranslatorAgent:
    """Translates English broadcast scripts to multiple target languages."""

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
    async def translate_single(self, english_script: str, target_language: str) -> str:
        """Translate an English broadcast script to a single target language."""
        await rate_limiter.acquire("llm")

        log.info(f"translating_to_{target_language}", input_words=len(english_script.split()))

        sys_prompt = TRANSLATOR_SYSTEM_PROMPT.replace("{language}", target_language)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": english_script},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        translated_script = response.choices[0].message.content
        log.info("translation_complete", language=target_language, output_chars=len(translated_script))
        return translated_script

    async def translate(self, english_script: str, target_languages: list[str] = None) -> dict[str, str]:
        """
        Translates to multiple languages concurrently.
        Defaults to Hindi for backwards compatibility if none specified.
        """
        import asyncio
        if target_languages is None:
            target_languages = ["Hindi"]
            
        tasks = []
        for lang in target_languages:
            tasks.append(self.translate_single(english_script, lang))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        translations = {}
        for lang, result in zip(target_languages, results):
            if isinstance(result, Exception):
                log.error("translation_failed", language=lang, error=str(result))
                translations[lang] = ""
            else:
                translations[lang] = result
                
        return translations
