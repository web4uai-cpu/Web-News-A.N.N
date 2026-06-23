"""
A.N.N. Feedback Loop Controller
Orchestrates the full self-improvement cycle:
  1. Collect agent performance metrics
  2. Identify underperforming agents
  3. Analyze failure patterns
  4. Evolve prompts
  5. Deploy A/B tests
  6. Auto-promote winners
"""

import asyncio
from datetime import datetime, timezone

from ai.self_improve.performance_tracker import tracker, RunRecord
from ai.self_improve.prompt_evolver import evolver
from ai.self_improve.auto_tuner import auto_tuner

from utils.logger import get_logger

log = get_logger("feedback_loop")


class FeedbackLoopController:
    def __init__(self):
        self.cycle_count = 0
        self.last_cycle_at: str | None = None
        self._improvement_history: list[dict] = []

    async def run_cycle(self) -> dict:
        self.cycle_count += 1
        self.last_cycle_at = datetime.now(timezone.utc).isoformat()

        log.info("improvement_cycle_started", cycle=self.cycle_count)

        all_metrics = tracker.get_all_metrics()
        actions_taken: list[dict] = []

        for agent_name, metrics in all_metrics.items():
            if metrics.total_runs < 50:
                continue

            should = auto_tuner.should_evolve_agent(
                agent_name, metrics.avg_quality_score, metrics.total_runs
            )

            if not should:
                continue

            failure_modes = self._extract_failure_modes(agent_name)
            positive_patterns = self._extract_positive_patterns(agent_name)

            try:
                new_variant = await evolver.evolve(
                    agent_name=agent_name,
                    failure_modes=failure_modes,
                    positive_patterns=positive_patterns,
                    avg_quality=metrics.avg_quality_score,
                )

                current = evolver.get_active_prompt(agent_name)
                test = auto_tuner.start_ab_test(
                    agent_name=agent_name,
                    variant_a=evolver._active[agent_name].id,
                    variant_b=new_variant.id,
                )

                actions_taken.append({
                    "agent": agent_name,
                    "action": "evolved_and_testing",
                    "new_version": new_variant.version,
                    "test_id": test.id,
                    "current_quality": metrics.avg_quality_score,
                    "trend": metrics.trend,
                })

                log.info(
                    "agent_evolved",
                    agent=agent_name,
                    new_version=new_variant.version,
                    test_id=test.id,
                )

            except Exception as e:
                log.error("evolution_failed", agent=agent_name, error=str(e))
                actions_taken.append({
                    "agent": agent_name,
                    "action": "evolution_failed",
                    "error": str(e),
                })

        concluded_tests = self._check_concluded_tests()
        for test_result in concluded_tests:
            actions_taken.append(test_result)

        cycle_report = {
            "cycle": self.cycle_count,
            "timestamp": self.last_cycle_at,
            "agents_evaluated": len(all_metrics),
            "actions_taken": actions_taken,
            "active_ab_tests": len(auto_tuner.get_active_tests()),
        }

        self._improvement_history.append(cycle_report)
        log.info("improvement_cycle_completed", cycle=self.cycle_count, actions=len(actions_taken))
        return cycle_report

    def _extract_failure_modes(self, agent_name: str) -> list[str]:
        records = tracker._records.get(agent_name, [])
        failed = [r for r in records[-100:] if not r.success]
        errors = [r.error for r in failed if r.error]
        unique_errors = list(set(errors))[:5]
        return unique_errors or ["no specific failures identified"]

    def _extract_positive_patterns(self, agent_name: str) -> list[str]:
        records = tracker._records.get(agent_name, [])
        high_quality = [r for r in records[-100:] if r.quality_score >= 8.0]
        if not high_quality:
            return []
        return [f"{len(high_quality)} runs scored 8.0+"]

    def _check_concluded_tests(self) -> list[dict]:
        results = []
        for test_id, test in list(auto_tuner._tests.items()):
            if test.status != "concluded" or test.winner in ("", "no_significant_difference"):
                continue

            winning_variant = test.variant_a if test.winner == "a" else test.variant_b
            promoted = evolver.promote(test.agent_name, winning_variant)

            results.append({
                "agent": test.agent_name,
                "action": "test_concluded",
                "test_id": test.id,
                "winner": test.winner,
                "promoted": promoted,
            })

        return results

    def get_improvement_history(self) -> list[dict]:
        return self._improvement_history

    def get_agent_evolution_timeline(self, agent_name: str) -> dict:
        variants = evolver.get_history(agent_name)
        metrics = tracker.get_metrics(agent_name)
        active_tests = [
            t for t in auto_tuner.get_active_tests()
            if t.agent_name == agent_name
        ]

        return {
            "agent": agent_name,
            "current_quality": metrics.avg_quality_score,
            "trend": metrics.trend,
            "total_variants": len(variants),
            "active_tests": len(active_tests),
            "generations": [
                {
                    "version": v.version,
                    "quality": v.avg_quality_score,
                    "samples": v.sample_count,
                    "is_champion": v.is_champion,
                    "created_at": v.created_at,
                }
                for v in variants
            ],
        }


feedback_controller = FeedbackLoopController()
