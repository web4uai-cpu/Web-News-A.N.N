"""
A.N.N. Agent Memory System
Short-term (Redis) and long-term (in-memory/Postgres) memory for agents.
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

import redis.asyncio as aioredis


# ═══════════════════════════════════════════════════════════
# SHORT-TERM MEMORY (Redis-backed, session-scoped)
# ═══════════════════════════════════════════════════════════

class ShortTermMemory:
    """Redis-backed short-term memory for deduplication, batch context, and recent history."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    # ── Dedup Buffer ──────────────────────────────────────

    async def check_seen(self, text: str) -> bool:
        """Check if we've processed a similar article recently."""
        r = await self._get_redis()
        if not r:
            return False
        text_hash = hashlib.md5(text[:500].encode()).hexdigest()
        return await r.sismember("ann:dedup:hashes", text_hash)

    async def mark_seen(self, text: str, ttl_hours: int = 24):
        """Mark an article as processed."""
        r = await self._get_redis()
        if not r:
            return
        text_hash = hashlib.md5(text[:500].encode()).hexdigest()
        await r.sadd("ann:dedup:hashes", text_hash)
        await r.expire("ann:dedup:hashes", ttl_hours * 3600)

    # ── Batch Context ─────────────────────────────────────

    async def set_batch_context(self, batch_id: str, data: dict, ttl_seconds: int = 3600):
        r = await self._get_redis()
        if not r:
            return
        await r.setex(f"ann:batch:{batch_id}", ttl_seconds, json.dumps(data))

    async def get_batch_context(self, batch_id: str) -> dict | None:
        r = await self._get_redis()
        if not r:
            return None
        raw = await r.get(f"ann:batch:{batch_id}")
        return json.loads(raw) if raw else None

    # ── Recent Rejections ─────────────────────────────────

    async def log_rejection(self, reason: str):
        r = await self._get_redis()
        if not r:
            return
        entry = json.dumps({"reason": reason, "time": datetime.utcnow().isoformat()})
        await r.lpush("ann:rejections", entry)
        await r.ltrim("ann:rejections", 0, 49)

    async def get_recent_rejections(self, limit: int = 10) -> list[dict]:
        r = await self._get_redis()
        if not r:
            return []
        entries = await r.lrange("ann:rejections", 0, limit - 1)
        return [json.loads(e) for e in entries]


# ═══════════════════════════════════════════════════════════
# LONG-TERM MEMORY (In-memory with persistence hooks)
# ═══════════════════════════════════════════════════════════

@dataclass
class SourceReputation:
    source_name: str
    articles_processed: int = 0
    avg_relevance: float = 5.0
    avg_critic_score: float = 0.5
    legal_blocks: int = 0
    last_seen: str = ""

    def update(self, relevance: float, critic_passed: bool, legal_blocked: bool):
        self.articles_processed += 1
        alpha = 0.1
        self.avg_relevance = self.avg_relevance * (1 - alpha) + relevance * alpha
        self.avg_critic_score = self.avg_critic_score * (1 - alpha) + (1.0 if critic_passed else 0.0) * alpha
        if legal_blocked:
            self.legal_blocks += 1
        self.last_seen = datetime.utcnow().isoformat()


class LongTermMemory:
    """Persistent agent memory for source reputation, topic tracking, and quality baselines."""

    def __init__(self):
        self.source_reputation: dict[str, SourceReputation] = {}
        self.topic_frequency: dict[str, int] = defaultdict(int)
        self.quality_baselines: dict[str, list[float]] = defaultdict(list)
        self.translation_glossary: dict[str, dict[str, str]] = {}

    # ── Source Reputation ─────────────────────────────────

    def update_source(self, source: str, relevance: float, critic_passed: bool, legal_blocked: bool = False):
        if source not in self.source_reputation:
            self.source_reputation[source] = SourceReputation(source_name=source)
        self.source_reputation[source].update(relevance, critic_passed, legal_blocked)

    def get_source_score(self, source: str) -> float:
        rep = self.source_reputation.get(source)
        if not rep:
            return 5.0
        return rep.avg_relevance * 0.6 + rep.avg_critic_score * 10 * 0.4

    def get_all_sources(self) -> list[dict]:
        return [
            {
                "source": r.source_name,
                "articles": r.articles_processed,
                "avg_relevance": round(r.avg_relevance, 2),
                "critic_pass_rate": round(r.avg_critic_score * 100, 1),
                "legal_blocks": r.legal_blocks,
                "score": round(self.get_source_score(r.source_name), 2),
            }
            for r in sorted(self.source_reputation.values(), key=lambda x: x.articles_processed, reverse=True)
        ]

    # ── Topic Tracking ────────────────────────────────────

    def track_topic(self, category: str, headline: str):
        self.topic_frequency[category] += 1
        for word in headline.lower().split():
            if len(word) > 4:
                self.topic_frequency[f"word:{word}"] += 1

    def get_trending_topics(self, top_n: int = 10) -> list[tuple[str, int]]:
        word_topics = {k: v for k, v in self.topic_frequency.items() if k.startswith("word:")}
        sorted_topics = sorted(word_topics.items(), key=lambda x: x[1], reverse=True)
        return [(k.replace("word:", ""), v) for k, v in sorted_topics[:top_n]]

    # ── Quality Baselines ─────────────────────────────────

    def record_quality(self, category: str, score: float):
        self.quality_baselines[category].append(score)
        if len(self.quality_baselines[category]) > 100:
            self.quality_baselines[category] = self.quality_baselines[category][-100:]

    def get_baseline(self, category: str) -> float:
        scores = self.quality_baselines.get(category, [])
        if not scores:
            return 7.0
        return sum(scores) / len(scores)

    # ── Translation Glossary ──────────────────────────────

    def add_glossary_entry(self, english: str, language: str, translation: str):
        if english not in self.translation_glossary:
            self.translation_glossary[english] = {}
        self.translation_glossary[english][language] = translation

    def get_glossary(self, language: str) -> dict[str, str]:
        return {
            eng: trans.get(language, "")
            for eng, trans in self.translation_glossary.items()
            if language in trans
        }

    # ── Export ─────────────────────────────────────────────

    def export_state(self) -> dict:
        return {
            "sources": self.get_all_sources(),
            "trending": self.get_trending_topics(),
            "categories": {cat: round(self.get_baseline(cat), 2) for cat in self.quality_baselines},
            "glossary_size": sum(len(v) for v in self.translation_glossary.values()),
        }


# Global singletons
short_term = ShortTermMemory()
long_term = LongTermMemory()
