"""
A.N.N. Live Fact Verifier
Verifies claims against live sources: web search, knowledge bases, official APIs, and RAG.
"""

import json
import time
from datetime import datetime, timezone

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("live_verifier")


class EvidenceSource:
    def __init__(self, name: str = "", url: str = "", snippet: str = "", reliability: float = 0.0):
        self.name = name
        self.url = url
        self.snippet = snippet
        self.reliability = reliability
        self.retrieved_at = datetime.now(timezone.utc).isoformat()


class VerificationResult:
    def __init__(self, claim_text: str = ""):
        self.claim_text = claim_text
        self.verdict = "unverified"  # verified, disputed, unverifiable, partially_verified
        self.confidence = 0.0
        self.evidence: list[EvidenceSource] = []
        self.reasoning = ""
        self.sources_checked = 0
        self.verification_time_s = 0.0


VERDICT_PROMPT = """You are a senior fact-checker at a news organization.

Given a claim and evidence gathered from multiple sources, determine the verification status.

Claim: {claim}

Evidence:
{evidence}

Analyze the evidence and return JSON:
{{
    "verdict": "verified" | "disputed" | "partially_verified" | "unverifiable",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation (2-3 sentences)",
    "key_evidence": ["Most important evidence points"],
    "caveats": ["Any important caveats or nuances"]
}}"""


class LiveVerifier:
    def __init__(self):
        self.settings = get_settings()

    async def search_web(self, query: str, max_results: int = 5) -> list[EvidenceSource]:
        """Search the web for evidence supporting or refuting a claim."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_redirect": 1},
                )
                response.raise_for_status()
                data = response.json()

            sources = []
            for result in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(result, dict) and "Text" in result:
                    sources.append(EvidenceSource(
                        name="DuckDuckGo",
                        url=result.get("FirstURL", ""),
                        snippet=result.get("Text", ""),
                        reliability=0.6,
                    ))
            return sources
        except Exception as e:
            log.error("web_search_failed", error=str(e))
            return []

    async def check_knowledge_base(self, query: str) -> list[EvidenceSource]:
        """Query the RAG knowledge base for relevant stored facts."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"http://search-service:8006/api/v1/search/semantic",
                    json={"query": query, "limit": 5},
                )
                if response.status_code != 200:
                    return []
                data = response.json()

            return [
                EvidenceSource(
                    name="A.N.N. Knowledge Base",
                    url=f"/scripts/{r.get('id', '')}",
                    snippet=r.get("content", "")[:300],
                    reliability=0.7,
                )
                for r in data.get("results", [])
            ]
        except Exception:
            return []

    async def check_official_data(self, claim: str, entities: list[str]) -> list[EvidenceSource]:
        """Check official data sources (Wikipedia, Wikidata) for entity-based claims."""
        sources = []
        for entity in entities[:3]:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        "https://en.wikipedia.org/api/rest_v1/page/summary/" + entity.replace(" ", "_"),
                    )
                    if response.status_code == 200:
                        data = response.json()
                        sources.append(EvidenceSource(
                            name=f"Wikipedia: {entity}",
                            url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                            snippet=data.get("extract", "")[:400],
                            reliability=0.75,
                        ))
            except Exception:
                continue
        return sources

    async def verify_claim(self, claim_text: str, entities: list[str] | None = None) -> VerificationResult:
        t0 = time.time()
        result = VerificationResult(claim_text=claim_text)
        all_evidence: list[EvidenceSource] = []

        web_evidence = await self.search_web(claim_text)
        all_evidence.extend(web_evidence)

        kb_evidence = await self.check_knowledge_base(claim_text)
        all_evidence.extend(kb_evidence)

        if entities:
            official_evidence = await self.check_official_data(claim_text, entities)
            all_evidence.extend(official_evidence)

        result.evidence = all_evidence
        result.sources_checked = len(all_evidence)

        if not all_evidence:
            result.verdict = "unverifiable"
            result.confidence = 0.0
            result.reasoning = "No evidence found from any source."
            result.verification_time_s = round(time.time() - t0, 2)
            return result

        await rate_limiter.acquire("llm")

        evidence_text = "\n".join(
            f"[{e.name}] (reliability: {e.reliability}): {e.snippet}"
            for e in all_evidence
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": self.settings.llm_model,
                        "messages": [
                            {"role": "user", "content": VERDICT_PROMPT.format(
                                claim=claim_text, evidence=evidence_text
                            )},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                verdict_data = json.loads(response.json()["choices"][0]["message"]["content"])

            result.verdict = verdict_data.get("verdict", "unverifiable")
            result.confidence = verdict_data.get("confidence", 0.0)
            result.reasoning = verdict_data.get("reasoning", "")

        except Exception as e:
            result.verdict = "unverifiable"
            result.reasoning = f"Verdict generation failed: {str(e)}"
            log.error("verdict_generation_failed", error=str(e))

        result.verification_time_s = round(time.time() - t0, 2)
        log.info(
            "claim_verified",
            verdict=result.verdict,
            confidence=result.confidence,
            sources=result.sources_checked,
            time_s=result.verification_time_s,
        )
        return result

    async def verify_all_claims(self, claims: list) -> list[VerificationResult]:
        results = []
        for claim in claims:
            r = await self.verify_claim(claim.text, claim.entities)
            claim.verification_status = r.verdict
            claim.confidence = r.confidence
            claim.evidence = [{"name": e.name, "snippet": e.snippet} for e in r.evidence]
            results.append(r)
        return results
