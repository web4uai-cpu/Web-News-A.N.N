"""
A.N.N. OSINT Pipeline
Government intelligence: threat classification, entity resolution, geolocation, confidence scoring.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("osint")


class ThreatType(str, Enum):
    MILITARY = "military"
    CYBER = "cyber"
    POLITICAL = "political"
    ECONOMIC = "economic"
    ENVIRONMENTAL = "environmental"
    HUMANITARIAN = "humanitarian"
    TERRORISM = "terrorism"


class ThreatSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERIFIED = "verified"


GOV_SOURCES = [
    {"name": "UN Press Releases", "url": "https://press.un.org/en", "type": "international"},
    {"name": "NATO Updates", "url": "https://www.nato.int/cps/en/natohq/news.htm", "type": "military"},
    {"name": "OSCE Reports", "url": "https://www.osce.org/press-releases", "type": "regional"},
    {"name": "State Department", "url": "https://www.state.gov/press-releases/", "type": "government"},
    {"name": "GDELT Project", "url": "https://api.gdeltproject.org/api/v2/doc/doc", "type": "aggregator"},
]


class ThreatEvent:
    def __init__(self):
        self.id = str(uuid4())
        self.title = ""
        self.threat_type = ThreatType.POLITICAL
        self.severity = ThreatSeverity.MODERATE
        self.confidence = ConfidenceLevel.MODERATE
        self.entities: list[dict] = []
        self.location: dict = {}
        self.sources: list[str] = []
        self.source_count = 0
        self.summary = ""
        self.timestamp = datetime.now(timezone.utc).isoformat()


class ThreatClassificationAgent:
    def __init__(self):
        self.settings = get_settings()

    async def classify(self, text: str) -> dict:
        await rate_limiter.acquire("llm")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": (
                            "Classify this text by threat type and severity. "
                            "Return JSON: {\"threat_type\": str, \"severity\": \"low|moderate|high|critical\", "
                            "\"reasoning\": str, \"keywords\": []}"
                        )},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


class EntityResolutionAgent:
    def __init__(self):
        self.settings = get_settings()

    async def extract_entities(self, text: str) -> dict:
        await rate_limiter.acquire("llm")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": (
                            "Extract all named entities from this intelligence text. "
                            "Return JSON: {\"people\": [{\"name\": str, \"role\": str}], "
                            "\"organizations\": [{\"name\": str, \"type\": str}], "
                            "\"locations\": [{\"name\": str, \"type\": str, \"coordinates\": [lat, lon] | null}], "
                            "\"relationships\": [{\"source\": str, \"target\": str, \"type\": str}]}"
                        )},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


class GeolocationAgent:
    def __init__(self):
        self.settings = get_settings()

    async def geolocate(self, text: str) -> dict:
        await rate_limiter.acquire("llm")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": (
                            "Extract geographic locations from this text and provide coordinates. "
                            "Return JSON: {\"locations\": [{\"name\": str, \"country\": str, "
                            "\"lat\": float, \"lon\": float, \"confidence\": float}]}"
                        )},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def compute_confidence(source_count: int, source_agreement: float) -> ConfidenceLevel:
    if source_count >= 3 and source_agreement >= 0.9:
        return ConfidenceLevel.VERIFIED
    if source_count >= 2 and source_agreement >= 0.7:
        return ConfidenceLevel.HIGH
    if source_count >= 1 and source_agreement >= 0.5:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW
