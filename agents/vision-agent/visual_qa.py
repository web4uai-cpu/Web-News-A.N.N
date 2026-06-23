"""
A.N.N. Visual QA Agent
Answers questions about images and performs visual fact verification.
Used by the fact-checking pipeline to verify claims against visual evidence.
"""

import base64
import time
from pathlib import Path

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("visual_qa")


class VisualQAResult:
    def __init__(self):
        self.answer = ""
        self.confidence = 0.0
        self.evidence_found = False
        self.details: list[str] = []
        self.processing_time_s = 0.0


class VisualQAAgent:
    def __init__(self):
        self.settings = get_settings()

    async def ask_about_image(self, image_path: str, question: str) -> VisualQAResult:
        t0 = time.time()
        result = VisualQAResult()

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}.get(ext, "jpeg")

        await rate_limiter.acquire("llm")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": "gpt-4o",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Answer this question about the image. Be precise and factual.\n\nQuestion: {question}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{image_b64}", "detail": "high"}},
                            ],
                        }],
                        "temperature": 0.1,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                result.answer = response.json()["choices"][0]["message"]["content"]
                result.evidence_found = True

        except Exception as e:
            result.answer = f"Analysis failed: {str(e)}"
            log.error("visual_qa_failed", error=str(e))

        result.processing_time_s = round(time.time() - t0, 2)
        return result

    async def verify_image_claim(
        self, image_path: str, claim: str
    ) -> dict:
        await rate_limiter.acquire("llm")

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": (
                                "You are a visual fact-checker. Determine if the image supports, contradicts, or is irrelevant to the claim. "
                                "Return JSON: {\"verdict\": \"supports|contradicts|inconclusive|irrelevant\", \"confidence\": 0.0-1.0, "
                                "\"reasoning\": str, \"visual_evidence\": [str]}"
                            )},
                            {"role": "user", "content": [
                                {"type": "text", "text": f"Claim: {claim}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}", "detail": "high"}},
                            ]},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()

            import json
            return json.loads(response.json()["choices"][0]["message"]["content"])

        except Exception as e:
            log.error("image_claim_verification_failed", error=str(e))
            return {"verdict": "inconclusive", "confidence": 0.0, "reasoning": str(e), "visual_evidence": []}

    async def detect_manipulation(self, image_path: str) -> dict:
        await rate_limiter.acquire("llm")

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {"role": "system", "content": (
                                "Analyze this image for signs of AI generation or manipulation. "
                                "Return JSON: {\"is_likely_manipulated\": bool, \"confidence\": 0.0-1.0, "
                                "\"indicators\": [str], \"recommendation\": str}"
                            )},
                            {"role": "user", "content": [
                                {"type": "text", "text": "Is this image authentic or manipulated?"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}", "detail": "high"}},
                            ]},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()

            import json
            return json.loads(response.json()["choices"][0]["message"]["content"])

        except Exception as e:
            log.error("manipulation_detection_failed", error=str(e))
            return {"is_likely_manipulated": False, "confidence": 0.0, "indicators": [], "recommendation": str(e)}
