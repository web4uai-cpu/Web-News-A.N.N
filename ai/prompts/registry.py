"""
A.N.N. Prompt Registry — versioned prompt management with A/B testing.

Prompts are YAML files in ai/prompts/templates/ with versioning and variant support.
The registry loads prompts by name, picks variants for A/B tests, and tracks performance.
"""

import os
import random
import yaml
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path


@dataclass
class PromptVariant:
    name: str
    version: str
    content: str
    temperature: float = 0.5
    max_tokens: int = 2000
    is_default: bool = False


@dataclass
class PromptPerformance:
    variant_name: str
    total_uses: int = 0
    total_score: float = 0.0
    wins: int = 0

    @property
    def avg_score(self) -> float:
        return self.total_score / max(self.total_uses, 1)


class PromptRegistry:
    """Load, version, and A/B test prompts."""

    def __init__(self, prompts_dir: str | None = None):
        self.prompts_dir = prompts_dir or os.path.join(os.path.dirname(__file__), "templates")
        self._prompts: dict[str, list[PromptVariant]] = {}
        self._performance: dict[str, dict[str, PromptPerformance]] = defaultdict(dict)
        self._load_all()

    def _load_all(self):
        templates_dir = Path(self.prompts_dir)
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)
            return

        for path in templates_dir.glob("*.yaml"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data:
                    continue

                name = data.get("name", path.stem)
                variants = []
                for v in data.get("variants", []):
                    variants.append(PromptVariant(
                        name=v.get("name", "default"),
                        version=v.get("version", "1.0"),
                        content=v.get("content", ""),
                        temperature=v.get("temperature", 0.5),
                        max_tokens=v.get("max_tokens", 2000),
                        is_default=v.get("default", False),
                    ))

                if variants:
                    self._prompts[name] = variants
                    for v in variants:
                        self._performance[name][v.name] = PromptPerformance(variant_name=v.name)

            except Exception:
                pass

    def get(self, name: str, variant: str | None = None) -> PromptVariant | None:
        """Get a specific prompt variant, or the default."""
        variants = self._prompts.get(name, [])
        if not variants:
            return None

        if variant:
            for v in variants:
                if v.name == variant:
                    return v

        for v in variants:
            if v.is_default:
                return v

        return variants[0]

    def get_ab_variant(self, name: str) -> PromptVariant | None:
        """Select a variant for A/B testing (weighted random by performance)."""
        variants = self._prompts.get(name, [])
        if not variants:
            return None
        if len(variants) == 1:
            return variants[0]

        # Thompson sampling-inspired: prefer higher-scoring variants
        weights = []
        for v in variants:
            perf = self._performance[name].get(v.name)
            if perf and perf.total_uses > 5:
                weights.append(max(perf.avg_score, 0.1))
            else:
                weights.append(5.0)  # Exploration bonus for undertested variants

        total = sum(weights)
        probs = [w / total for w in weights]
        return random.choices(variants, weights=probs, k=1)[0]

    def record_score(self, name: str, variant_name: str, score: float):
        """Record a quality score for a prompt variant."""
        if name in self._performance and variant_name in self._performance[name]:
            perf = self._performance[name][variant_name]
            perf.total_uses += 1
            perf.total_score += score

    def get_performance(self, name: str) -> list[dict]:
        """Get performance stats for all variants of a prompt."""
        if name not in self._performance:
            return []
        return [
            {
                "variant": p.variant_name,
                "uses": p.total_uses,
                "avg_score": round(p.avg_score, 2),
            }
            for p in self._performance[name].values()
        ]

    def list_prompts(self) -> list[dict]:
        """List all registered prompts and their variants."""
        return [
            {
                "name": name,
                "variants": [{"name": v.name, "version": v.version, "default": v.is_default} for v in variants],
            }
            for name, variants in self._prompts.items()
        ]

    def register(self, name: str, variant: PromptVariant):
        """Register a prompt variant programmatically."""
        if name not in self._prompts:
            self._prompts[name] = []
        self._prompts[name].append(variant)
        self._performance[name][variant.name] = PromptPerformance(variant_name=variant.name)


# Global singleton
registry = PromptRegistry()
