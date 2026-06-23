"""
A.N.N. Auto-Tuner
Automated agent optimization loop: monitors performance, triggers evolution,
manages A/B tests, and auto-promotes winning variants.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from utils.logger import get_logger

log = get_logger("auto_tuner")


@dataclass
class ABTest:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_name: str = ""
    variant_a: str = ""
    variant_b: str = ""
    traffic_split: float = 0.5
    min_samples: int = 100
    samples_a: int = 0
    samples_b: int = 0
    quality_a: list[float] = field(default_factory=list)
    quality_b: list[float] = field(default_factory=list)
    status: str = "running"  # running, concluded, cancelled
    winner: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    concluded_at: str | None = None


@dataclass
class TuningConfig:
    quality_threshold: float = 7.0
    min_samples_before_evolve: int = 50
    ab_test_min_samples: int = 100
    significance_threshold: float = 0.05
    max_concurrent_tests: int = 3
    auto_promote: bool = True
    cooldown_runs: int = 200


class AutoTuner:
    def __init__(self, config: TuningConfig | None = None):
        self.config = config or TuningConfig()
        self._tests: dict[str, ABTest] = {}
        self._cooldowns: dict[str, int] = {}

    def start_ab_test(
        self, agent_name: str, variant_a: str, variant_b: str, traffic_split: float = 0.5
    ) -> ABTest:
        active_tests = [t for t in self._tests.values() if t.status == "running"]
        if len(active_tests) >= self.config.max_concurrent_tests:
            raise RuntimeError(f"Max {self.config.max_concurrent_tests} concurrent A/B tests allowed")

        test = ABTest(
            agent_name=agent_name,
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split,
            min_samples=self.config.ab_test_min_samples,
        )
        self._tests[test.id] = test
        log.info("ab_test_started", test_id=test.id, agent=agent_name)
        return test

    def assign_variant(self, test_id: str) -> str:
        test = self._tests.get(test_id)
        if not test or test.status != "running":
            return "a"

        import random
        return "a" if random.random() < test.traffic_split else "b"

    def record_result(self, test_id: str, variant: str, quality_score: float) -> None:
        test = self._tests.get(test_id)
        if not test or test.status != "running":
            return

        if variant == "a":
            test.samples_a += 1
            test.quality_a.append(quality_score)
        else:
            test.samples_b += 1
            test.quality_b.append(quality_score)

        if test.samples_a >= test.min_samples and test.samples_b >= test.min_samples:
            self._evaluate_test(test)

    def _evaluate_test(self, test: ABTest) -> None:
        from statistics import mean

        mean_a = mean(test.quality_a) if test.quality_a else 0
        mean_b = mean(test.quality_b) if test.quality_b else 0

        is_significant = self._is_statistically_significant(test.quality_a, test.quality_b)

        if is_significant:
            test.winner = "a" if mean_a > mean_b else "b"
            test.status = "concluded"
            test.concluded_at = datetime.now(timezone.utc).isoformat()

            log.info(
                "ab_test_concluded",
                test_id=test.id,
                winner=test.winner,
                mean_a=round(mean_a, 3),
                mean_b=round(mean_b, 3),
                agent=test.agent_name,
            )

            if self.config.auto_promote:
                self._cooldowns[test.agent_name] = self.config.cooldown_runs
        else:
            if test.samples_a + test.samples_b >= test.min_samples * 3:
                test.status = "concluded"
                test.winner = "no_significant_difference"
                test.concluded_at = datetime.now(timezone.utc).isoformat()
                log.info("ab_test_inconclusive", test_id=test.id, agent=test.agent_name)

    def _is_statistically_significant(
        self, scores_a: list[float], scores_b: list[float]
    ) -> bool:
        if len(scores_a) < 30 or len(scores_b) < 30:
            return False

        from statistics import mean, stdev
        from math import sqrt

        n_a, n_b = len(scores_a), len(scores_b)
        mean_a, mean_b = mean(scores_a), mean(scores_b)
        std_a, std_b = stdev(scores_a) if n_a > 1 else 0, stdev(scores_b) if n_b > 1 else 0

        if std_a == 0 and std_b == 0:
            return mean_a != mean_b

        se = sqrt((std_a**2 / n_a) + (std_b**2 / n_b))
        if se == 0:
            return False

        z = abs(mean_a - mean_b) / se
        return z > 1.96  # p < 0.05

    def get_active_tests(self) -> list[ABTest]:
        return [t for t in self._tests.values() if t.status == "running"]

    def get_test_results(self, test_id: str) -> ABTest | None:
        return self._tests.get(test_id)

    def should_evolve_agent(self, agent_name: str, current_quality: float, run_count: int) -> bool:
        cooldown = self._cooldowns.get(agent_name, 0)
        if cooldown > 0:
            self._cooldowns[agent_name] = cooldown - 1
            return False

        active = [t for t in self._tests.values() if t.agent_name == agent_name and t.status == "running"]
        if active:
            return False

        if run_count < self.config.min_samples_before_evolve:
            return False

        return current_quality < self.config.quality_threshold


auto_tuner = AutoTuner()
