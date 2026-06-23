"""
A.N.N. Content Moderation Service
Handles flagged content review queue, human-in-the-loop decisions, and audit logging.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from utils.logger import get_logger

log = get_logger("moderation")


class FlagType(str, Enum):
    COPYRIGHT = "copyright"
    DEFAMATION = "defamation"
    PII = "pii"
    BIAS = "bias"
    MISINFORMATION = "misinformation"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class ModerationFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    article_id: str
    flag_type: FlagType
    severity: Severity
    flagged_by: str = "legal_agent"
    excerpt: str = ""
    reason: str = ""
    status: ModerationStatus = ModerationStatus.PENDING
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: str
    entity_type: str
    entity_id: str
    actor: str
    details: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AutoBlockRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    rule_type: str
    pattern: str
    action: str = "block"
    enabled: bool = True
    created_by: str = ""


class ModerationService:
    def __init__(self):
        self._queue: list[ModerationFlag] = []
        self._audit_log: list[AuditEntry] = []
        self._auto_rules: list[AutoBlockRule] = []

    def flag_article(self, flag: ModerationFlag) -> ModerationFlag:
        self._queue.append(flag)
        self._log_audit("flag_created", "article", flag.article_id, flag.flagged_by, {
            "flag_type": flag.flag_type.value,
            "severity": flag.severity.value,
        })
        log.info("article_flagged", article_id=flag.article_id, flag_type=flag.flag_type.value)
        return flag

    def review(
        self, flag_id: str, decision: ModerationStatus, reviewer: str, notes: str = ""
    ) -> ModerationFlag | None:
        for flag in self._queue:
            if flag.id == flag_id and flag.status == ModerationStatus.PENDING:
                flag.status = decision
                flag.reviewed_by = reviewer
                flag.reviewed_at = datetime.now(timezone.utc).isoformat()

                self._log_audit("moderation_decision", "flag", flag_id, reviewer, {
                    "decision": decision.value,
                    "article_id": flag.article_id,
                    "notes": notes,
                })
                log.info("moderation_decision", flag_id=flag_id, decision=decision.value)
                return flag
        return None

    def get_pending(self) -> list[ModerationFlag]:
        return [f for f in self._queue if f.status == ModerationStatus.PENDING]

    def get_audit_log(self, limit: int = 100) -> list[AuditEntry]:
        return self._audit_log[-limit:]

    def add_auto_rule(self, rule: AutoBlockRule) -> AutoBlockRule:
        self._auto_rules.append(rule)
        self._log_audit("auto_rule_created", "rule", rule.id, rule.created_by, {
            "rule_type": rule.rule_type,
            "pattern": rule.pattern,
        })
        return rule

    def check_auto_rules(self, text: str, source: str = "") -> list[AutoBlockRule]:
        triggered = []
        for rule in self._auto_rules:
            if not rule.enabled:
                continue
            if rule.rule_type == "keyword" and rule.pattern.lower() in text.lower():
                triggered.append(rule)
            elif rule.rule_type == "source" and rule.pattern.lower() in source.lower():
                triggered.append(rule)
        return triggered

    def _log_audit(self, action: str, entity_type: str, entity_id: str, actor: str, details: dict) -> None:
        entry = AuditEntry(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            details=details,
        )
        self._audit_log.append(entry)
