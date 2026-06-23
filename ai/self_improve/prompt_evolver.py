"""
A.N.N. Prompt Evolver
Automatically evolves agent prompts based on performance data.
Uses A/B testing results and quality feedback to generate improved prompt variants.
"""

import json
import time
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("prompt_evolver")


@dataclass
class PromptVariant:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_name: str = ""
    version: str = ""
    content: str = ""
    parent_id: str | None = None
    generation: int = 0
    avg_quality_score: float = 0.0
    sample_count: int = 0
    is_active: bool = False
    is_champion: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evolution_reason: str = ""


EVOLUTION_PROMPT = """You are an expert prompt engineer optimizing prompts for an AI news pipeline.

Current prompt (agent: {agent_name}):
```
{current_prompt}
```

Performance data:
- Average quality score: {avg_quality} / 10
- Common failure modes: {failure_modes}
- Positive feedback patterns: {positive_patterns}

Task: Generate an improved version of this prompt that addresses the weaknesses while preserving strengths.

Rules:
1. Maintain the same output format requirements
2. Keep the prompt under {max_tokens} tokens
3. Be specific about what to improve
4. Don't change the fundamental role or task

Return JSON:
{{
    "improved_prompt": "...",
    "changes_made": ["list of specific changes"],
    "rationale": "why these changes should improve quality",
    "expected_improvement": "what metric should improve"
}}"""


class PromptEvolver:
    def __init__(self):
        self.settings = get_settings()
        self._variants: dict[str, list[PromptVariant]] = {}
        self._active: dict[str, PromptVariant] = {}

    def register_prompt(self, agent_name: str, content: str, version: str = "v1") -> PromptVariant:
        variant = PromptVariant(
            agent_name=agent_name,
            version=version,
            content=content,
            is_active=True,
            is_champion=True,
        )
        if agent_name not in self._variants:
            self._variants[agent_name] = []
        self._variants[agent_name].append(variant)
        self._active[agent_name] = variant
        return variant

    def get_active_prompt(self, agent_name: str) -> str:
        active = self._active.get(agent_name)
        return active.content if active else ""

    async def evolve(
        self,
        agent_name: str,
        failure_modes: list[str],
        positive_patterns: list[str],
        avg_quality: float,
        max_tokens: int = 800,
    ) -> PromptVariant:
        current = self._active.get(agent_name)
        if not current:
            raise ValueError(f"No active prompt registered for {agent_name}")

        await rate_limiter.acquire("llm")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": self.settings.llm_model,
                        "messages": [
                            {"role": "user", "content": EVOLUTION_PROMPT.format(
                                agent_name=agent_name,
                                current_prompt=current.content,
                                avg_quality=round(avg_quality, 2),
                                failure_modes=", ".join(failure_modes) or "none identified",
                                positive_patterns=", ".join(positive_patterns) or "none identified",
                                max_tokens=max_tokens,
                            )},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = json.loads(response.json()["choices"][0]["message"]["content"])

        except Exception as e:
            log.error("prompt_evolution_failed", agent=agent_name, error=str(e))
            raise

        new_version = f"v{current.generation + 2}"
        new_variant = PromptVariant(
            agent_name=agent_name,
            version=new_version,
            content=data["improved_prompt"],
            parent_id=current.id,
            generation=current.generation + 1,
            evolution_reason=data.get("rationale", ""),
        )

        self._variants[agent_name].append(new_variant)

        log.info(
            "prompt_evolved",
            agent=agent_name,
            from_version=current.version,
            to_version=new_version,
            changes=data.get("changes_made", []),
        )
        return new_variant

    def promote(self, agent_name: str, variant_id: str) -> bool:
        variants = self._variants.get(agent_name, [])
        for v in variants:
            if v.id == variant_id:
                old_champion = self._active.get(agent_name)
                if old_champion:
                    old_champion.is_champion = False
                    old_champion.is_active = False

                v.is_champion = True
                v.is_active = True
                self._active[agent_name] = v

                log.info("prompt_promoted", agent=agent_name, variant=variant_id, version=v.version)
                return True
        return False

    def get_history(self, agent_name: str) -> list[PromptVariant]:
        return self._variants.get(agent_name, [])

    def should_evolve(self, agent_name: str, current_quality: float, threshold: float = 7.0) -> bool:
        if current_quality >= threshold:
            return False
        current = self._active.get(agent_name)
        if not current:
            return False
        if current.sample_count < 50:
            return False
        return True


evolver = PromptEvolver()
