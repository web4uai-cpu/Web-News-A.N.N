"""
A.N.N. Claim Extractor
Extracts verifiable claims from news text for fact-checking pipeline.
"""

import json
import time

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("claim_extractor")

EXTRACTION_PROMPT = """You are a fact-checking analyst. Extract all verifiable factual claims from this text.

For each claim, provide:
- claim: The exact factual assertion (one sentence)
- type: "statistic", "quote", "event", "attribution", "prediction"
- verifiability: "high" (can be checked against public data), "medium" (needs investigation), "low" (subjective)
- entities: list of named entities in the claim
- requires_sources: list of source types needed to verify (e.g., "government_data", "company_filing", "news_archive")

Return JSON: {"claims": [...]}
Only extract claims that can be independently verified. Skip opinions, analysis, and predictions."""


class Claim:
    def __init__(self, text: str = "", claim_type: str = "", verifiability: str = "medium"):
        self.text = text
        self.claim_type = claim_type
        self.verifiability = verifiability
        self.entities: list[str] = []
        self.requires_sources: list[str] = []
        self.verification_status = "pending"
        self.evidence: list[dict] = []
        self.confidence = 0.0


class ClaimExtractor:
    def __init__(self):
        self.settings = get_settings()

    async def extract_claims(self, text: str) -> list[Claim]:
        t0 = time.time()
        await rate_limiter.acquire("llm")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": self.settings.llm_model,
                        "messages": [
                            {"role": "system", "content": EXTRACTION_PROMPT},
                            {"role": "user", "content": text[:4000]},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = json.loads(response.json()["choices"][0]["message"]["content"])

        except Exception as e:
            log.error("claim_extraction_failed", error=str(e))
            return []

        claims = []
        for item in data.get("claims", []):
            claim = Claim(
                text=item.get("claim", ""),
                claim_type=item.get("type", ""),
                verifiability=item.get("verifiability", "medium"),
            )
            claim.entities = item.get("entities", [])
            claim.requires_sources = item.get("requires_sources", [])
            claims.append(claim)

        log.info("claims_extracted", count=len(claims), time_s=round(time.time() - t0, 2))
        return claims

    async def prioritize_claims(self, claims: list[Claim]) -> list[Claim]:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(claims, key=lambda c: priority_order.get(c.verifiability, 1))
