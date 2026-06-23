"""
A.N.N. Agent Performance Tracker
Tracks per-agent metrics across pipeline runs for self-improvement loops.
Metrics: latency, quality scores, error rates, cost, token usage.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, stdev

from utils.logger import get_logger

log = get_logger("performance_tracker")


@dataclass
class AgentMetrics:
    agent_name: str = ""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    avg_latency_s: float = 0.0
    p95_latency_s: float = 0.0
    avg_quality_score: float = 0.0
    avg_tokens_used: int = 0
    total_cost_usd: float = 0.0
    error_rate: float = 0.0
    trend: str = "stable"  # improving, degrading, stable


@dataclass
class RunRecord:
    agent_name: str
    run_id: str = ""
    prompt_version: str = "default"
    latency_s: float = 0.0
    quality_score: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)


TOKEN_COSTS = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gpt-image-1": {"per_image": 0.04},
}


class PerformanceTracker:
    def __init__(self, window_size: int = 500):
        self._records: dict[str, list[RunRecord]] = defaultdict(list)
        self._window_size = window_size

    def record(self, run: RunRecord) -> None:
        records = self._records[run.agent_name]
        records.append(run)
        if len(records) > self._window_size * 2:
            self._records[run.agent_name] = records[-self._window_size:]

        log.info(
            "agent_run_recorded",
            agent=run.agent_name,
            latency=run.latency_s,
            quality=run.quality_score,
            success=run.success,
        )

    def get_metrics(self, agent_name: str) -> AgentMetrics:
        records = self._records.get(agent_name, [])
        if not records:
            return AgentMetrics(agent_name=agent_name)

        recent = records[-self._window_size:]
        latencies = [r.latency_s for r in recent if r.success]
        qualities = [r.quality_score for r in recent if r.quality_score > 0]

        metrics = AgentMetrics(
            agent_name=agent_name,
            total_runs=len(recent),
            successful_runs=sum(1 for r in recent if r.success),
            failed_runs=sum(1 for r in recent if not r.success),
            avg_latency_s=round(mean(latencies), 3) if latencies else 0.0,
            p95_latency_s=round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else (latencies[0] if latencies else 0.0), 3),
            avg_quality_score=round(mean(qualities), 3) if qualities else 0.0,
            avg_tokens_used=int(mean(r.tokens_in + r.tokens_out for r in recent)),
            total_cost_usd=round(sum(r.cost_usd for r in recent), 4),
            error_rate=round(sum(1 for r in recent if not r.success) / len(recent), 4),
        )

        metrics.trend = self._compute_trend(qualities)
        return metrics

    def get_all_metrics(self) -> dict[str, AgentMetrics]:
        return {name: self.get_metrics(name) for name in self._records}

    def get_comparison(self, agent_name: str, prompt_a: str, prompt_b: str) -> dict:
        records = self._records.get(agent_name, [])
        a_records = [r for r in records if r.prompt_version == prompt_a]
        b_records = [r for r in records if r.prompt_version == prompt_b]

        def summarize(recs: list[RunRecord]) -> dict:
            if not recs:
                return {"count": 0}
            qualities = [r.quality_score for r in recs if r.quality_score > 0]
            latencies = [r.latency_s for r in recs if r.success]
            return {
                "count": len(recs),
                "avg_quality": round(mean(qualities), 3) if qualities else 0.0,
                "avg_latency": round(mean(latencies), 3) if latencies else 0.0,
                "error_rate": round(sum(1 for r in recs if not r.success) / len(recs), 4),
            }

        return {
            "agent": agent_name,
            prompt_a: summarize(a_records),
            prompt_b: summarize(b_records),
            "winner": self._determine_winner(a_records, b_records),
        }

    def _compute_trend(self, scores: list[float]) -> str:
        if len(scores) < 20:
            return "stable"
        recent = scores[-20:]
        older = scores[-40:-20] if len(scores) >= 40 else scores[:20]
        if not older:
            return "stable"
        diff = mean(recent) - mean(older)
        if diff > 0.05:
            return "improving"
        if diff < -0.05:
            return "degrading"
        return "stable"

    def _determine_winner(self, a: list[RunRecord], b: list[RunRecord]) -> str:
        if not a or not b:
            return "insufficient_data"
        q_a = mean(r.quality_score for r in a if r.quality_score > 0) if any(r.quality_score > 0 for r in a) else 0
        q_b = mean(r.quality_score for r in b if r.quality_score > 0) if any(r.quality_score > 0 for r in b) else 0
        if abs(q_a - q_b) < 0.03:
            return "no_significant_difference"
        return "a" if q_a > q_b else "b"


tracker = PerformanceTracker()
