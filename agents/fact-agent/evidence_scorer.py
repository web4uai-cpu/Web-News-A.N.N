"""
A.N.N. Evidence Scorer
Aggregates verification results into an overall fact-check score for a pipeline run.
"""

from dataclasses import dataclass, field

from utils.logger import get_logger

log = get_logger("evidence_scorer")

SOURCE_RELIABILITY = {
    "government_official": 0.95,
    "academic_journal": 0.90,
    "wire_service": 0.85,
    "wikipedia": 0.75,
    "major_news_outlet": 0.80,
    "knowledge_base": 0.70,
    "web_search": 0.60,
    "social_media": 0.30,
    "unknown": 0.40,
}


@dataclass
class FactCheckReport:
    total_claims: int = 0
    verified: int = 0
    disputed: int = 0
    partially_verified: int = 0
    unverifiable: int = 0
    overall_score: float = 0.0
    confidence: float = 0.0
    grade: str = ""
    flags: list[str] = field(default_factory=list)
    claim_details: list[dict] = field(default_factory=list)


GRADE_THRESHOLDS = [
    (0.90, "A", "Highly reliable — strong evidence supports all major claims"),
    (0.75, "B", "Mostly reliable — minor claims unverified"),
    (0.60, "C", "Mixed — some claims lack sufficient evidence"),
    (0.40, "D", "Unreliable — significant claims disputed or unverified"),
    (0.00, "F", "Failing — majority of claims are disputed or fabricated"),
]


class EvidenceScorer:
    def score_report(self, verification_results: list) -> FactCheckReport:
        report = FactCheckReport()
        report.total_claims = len(verification_results)

        if not verification_results:
            report.overall_score = 0.5
            report.confidence = 0.0
            report.grade = "N/A"
            return report

        weighted_scores = []
        for result in verification_results:
            verdict = result.verdict if hasattr(result, "verdict") else result.get("verdict", "")
            conf = result.confidence if hasattr(result, "confidence") else result.get("confidence", 0.0)

            verdict_score = {
                "verified": 1.0,
                "partially_verified": 0.6,
                "unverifiable": 0.3,
                "disputed": 0.0,
            }.get(verdict, 0.3)

            weighted_scores.append(verdict_score * max(conf, 0.1))

            if verdict == "verified":
                report.verified += 1
            elif verdict == "disputed":
                report.disputed += 1
            elif verdict == "partially_verified":
                report.partially_verified += 1
            else:
                report.unverifiable += 1

            report.claim_details.append({
                "claim": result.claim_text if hasattr(result, "claim_text") else result.get("claim", ""),
                "verdict": verdict,
                "confidence": conf,
            })

        report.overall_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0
        report.confidence = sum(
            r.confidence if hasattr(r, "confidence") else r.get("confidence", 0.0)
            for r in verification_results
        ) / len(verification_results)

        for threshold, grade, _ in GRADE_THRESHOLDS:
            if report.overall_score >= threshold:
                report.grade = grade
                break

        if report.disputed > 0:
            report.flags.append(f"{report.disputed} claim(s) disputed by evidence")
        if report.unverifiable > report.total_claims * 0.5:
            report.flags.append("More than 50% of claims could not be independently verified")
        if report.overall_score < 0.4:
            report.flags.append("EDITORIAL REVIEW RECOMMENDED — low fact-check score")

        log.info(
            "fact_check_scored",
            total=report.total_claims,
            verified=report.verified,
            disputed=report.disputed,
            score=round(report.overall_score, 3),
            grade=report.grade,
        )
        return report
