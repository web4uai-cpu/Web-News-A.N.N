"""
A.N.N. Translation Agent
Multi-language translation with glossary support and RTL handling.
"""

import json
from enum import Enum

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("translation_agent")

SUPPORTED_LANGUAGES = {
    "hi": {"name": "Hindi", "native": "हिन्दी", "dir": "ltr"},
    "es": {"name": "Spanish", "native": "Español", "dir": "ltr"},
    "fr": {"name": "French", "native": "Français", "dir": "ltr"},
    "ar": {"name": "Arabic", "native": "العربية", "dir": "rtl"},
}

GLOSSARY = {
    "hi": {
        "Apple": "एपल",
        "Google": "गूगल",
        "Microsoft": "माइक्रोसॉफ्ट",
        "Tesla": "टेस्ला",
        "NASA": "नासा",
        "United Nations": "संयुक्त राष्ट्र",
        "White House": "व्हाइट हाउस",
        "Wall Street": "वॉल स्ट्रीट",
    },
    "es": {
        "White House": "Casa Blanca",
        "United Nations": "Naciones Unidas",
        "Wall Street": "Wall Street",
    },
    "fr": {
        "White House": "Maison-Blanche",
        "United Nations": "Nations Unies",
        "Wall Street": "Wall Street",
    },
    "ar": {
        "White House": "البيت الأبيض",
        "United Nations": "الأمم المتحدة",
        "Wall Street": "وول ستريت",
        "Apple": "آبل",
        "Google": "غوغل",
    },
}


class TranslationAgent:
    def __init__(self):
        self.settings = get_settings()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=3, max=30))
    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> dict:
        if target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {target_lang}")

        await rate_limiter.acquire("llm")

        lang_info = SUPPORTED_LANGUAGES[target_lang]
        glossary = GLOSSARY.get(target_lang, {})
        glossary_str = "\n".join(f'  "{k}" → "{v}"' for k, v in glossary.items())

        system_prompt = f"""You are a professional news translator for A.N.N. (AI News Network).
Translate the following broadcast script from {source_lang.upper()} to {lang_info['name']} ({lang_info['native']}).

Rules:
- Maintain broadcast tone and pacing
- Preserve [PAUSE] markers exactly as-is
- Use the glossary for proper nouns:
{glossary_str}
- Keep numbers, dates, and units in their localized format
- For Arabic: use Modern Standard Arabic (MSA)
- Output ONLY the translated text, no explanations"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )
            response.raise_for_status()
            data = response.json()

        translated = data["choices"][0]["message"]["content"].strip()
        word_count = len(translated.split())

        log.info(
            "translation_complete",
            target_lang=target_lang,
            source_len=len(text),
            translated_len=len(translated),
            word_count=word_count,
        )

        return {
            "translated_text": translated,
            "target_lang": target_lang,
            "direction": lang_info["dir"],
            "word_count": word_count,
        }

    async def translate_all(self, text: str, languages: list[str] | None = None) -> dict[str, dict]:
        langs = languages or list(SUPPORTED_LANGUAGES.keys())
        results = {}
        for lang in langs:
            try:
                results[lang] = await self.translate(text, lang)
            except Exception as e:
                log.error("translation_failed", target_lang=lang, error=str(e))
                results[lang] = {"error": str(e), "target_lang": lang}
        return results
