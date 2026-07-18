"""
A.N.N. B2B Database Module
Using SQLAlchemy + aiosqlite for high-performance, async API Key management.
Tracks enterprise clients, their monthly billing cycles, and API quotas.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime, Float, Text
from datetime import datetime, timedelta
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ann_enterprise.db")
SQLITE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

_raw_url = os.getenv("DATABASE_URL")

if not _raw_url:
    DATABASE_URL = SQLITE_URL
else:
    if _raw_url.startswith("postgres://"):
        DATABASE_URL = _raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif _raw_url.startswith("postgresql://"):
        DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = _raw_url


def _build_engine(url: str):
    kwargs = {"echo": False}
    if "postgresql" in url:
        kwargs.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,  # transparently recycle stale Railway connections
        })
    return create_async_engine(url, **kwargs)


engine = _build_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

class BroadcastScriptRow(Base):
    __tablename__ = "broadcast_scripts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    headline: Mapped[str] = mapped_column(String)
    english_script: Mapped[str] = mapped_column(String)
    hindi_script: Mapped[str] = mapped_column(String, default="")
    translations_json: Mapped[str] = mapped_column(String, default="{}")
    category: Mapped[str] = mapped_column(String, default="general")
    source_url: Mapped[str] = mapped_column(String, default="")
    word_count_en: Mapped[int] = mapped_column(Integer, default=0)
    word_count_hi: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentMetricRow(Base):
    __tablename__ = "agent_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="completed")
    latency_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MediaJobRow(Base):
    __tablename__ = "media_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    script_id: Mapped[str] = mapped_column(String, index=True)
    headline: Mapped[str] = mapped_column(String, default="")
    media_type: Mapped[str] = mapped_column(String, default="audio")
    language: Mapped[str] = mapped_column(String, default="en")
    status: Mapped[str] = mapped_column(String, default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[str] = mapped_column(String, default="--")
    output_url: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClientAPIKey(Base):
    """
    Represents an Enterprise B2B Client paying for news feed access.
    """
    __tablename__ = "client_api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_name: Mapped[str] = mapped_column(String, index=True)
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)  # SHA-256 hash of the raw key
    key_prefix: Mapped[str] = mapped_column(String, default="", nullable=True)  # displayable prefix, e.g. "ann_pro_ab12…"
    plan_tier: Mapped[str] = mapped_column(String, default="standard")  # e.g. "free", "standard", "enterprise"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Quota Limits (Requests allowed per billing cycle)
    monthly_quota: Mapped[int] = mapped_column(Integer, default=1000)
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Billing/Webhook Settings
    webhook_url: Mapped[str] = mapped_column(String, nullable=True)
    webhook_secret: Mapped[str] = mapped_column(String, nullable=True)  # HMAC key for signing outbound webhooks
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

def _alembic_config():
    """Build an Alembic Config pointed at backend/alembic.ini."""
    from alembic.config import Config
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    return cfg


def _run_alembic_sync(needs_stamp: bool):
    """
    Synchronous Alembic runner (executed in a worker thread — Alembic's env.py
    calls asyncio.run() internally, which cannot run inside our event loop).

    ``needs_stamp`` adopts a pre-existing, un-stamped schema by stamping it to
    head first; then any newer migrations are applied. This makes Alembic the
    single source of truth for the Postgres schema going forward — no more
    ad-hoc ALTER TABLE on startup.
    """
    from alembic import command

    cfg = _alembic_config()
    if needs_stamp:
        command.stamp(cfg, "head")
    command.upgrade(cfg, "head")


def _inspect_migration_state(sync_conn) -> bool:
    """Return True if the DB has our tables but no Alembic stamp (needs adopting)."""
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import inspect
    has_version = MigrationContext.configure(sync_conn).get_current_revision() is not None
    has_tables = inspect(sync_conn).has_table("broadcast_scripts")
    return has_tables and not has_version


async def init_db():
    """
    Bring the schema up to date. Postgres is Alembic-managed (source of truth);
    dev SQLite uses create_all. In development an unreachable remote DB falls
    back to local SQLite; in production a DB failure is fatal — never silently
    serve SQLite.
    """
    global engine, AsyncSessionLocal, DATABASE_URL
    import asyncio
    import logging
    is_production = os.getenv("ENV", "development").lower() == "production"

    if is_production and "sqlite" in DATABASE_URL:
        logging.getLogger(__name__).warning(
            "ENV=production but DATABASE_URL is not set — running on SQLite is not supported for production."
        )

    if "sqlite" not in DATABASE_URL:
        # Postgres: run Alembic migrations (in a thread — env.py uses asyncio.run).
        try:
            async with engine.connect() as conn:
                needs_stamp = await conn.run_sync(_inspect_migration_state)
            await asyncio.to_thread(_run_alembic_sync, needs_stamp)
        except Exception:
            if is_production:
                raise
            logging.getLogger(__name__).warning("Remote DB unreachable, falling back to local SQLite (development only)")
            DATABASE_URL = SQLITE_URL
            engine = _build_engine(SQLITE_URL)
            AsyncSessionLocal.configure(bind=engine)

    if "sqlite" in DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Older local SQLite files predate newer columns — add them in place.
        from sqlalchemy import text
        for ddl in (
            "ALTER TABLE client_api_keys ADD COLUMN key_prefix VARCHAR DEFAULT ''",
            "ALTER TABLE client_api_keys ADD COLUMN webhook_secret VARCHAR",
            "ALTER TABLE broadcast_scripts ADD COLUMN translations_json VARCHAR DEFAULT '{}'",
        ):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(ddl))
            except Exception:
                pass

    # Seed a demo key for local development only — never in production.
    if os.getenv("ENV", "development").lower() == "development":
        from core.security import hash_api_key, key_prefix
        demo_raw = "ann_demo_key_777"
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ClientAPIKey).where(ClientAPIKey.api_key.in_([demo_raw, hash_api_key(demo_raw)]))
            )
            if not result.scalars().first():
                demo_client = ClientAPIKey(
                    client_name="Demo Developer Client",
                    api_key=hash_api_key(demo_raw),
                    key_prefix=key_prefix(demo_raw),
                    plan_tier="enterprise",
                    monthly_quota=50000,
                )
                session.add(demo_client)
                await session.commit()

    # Seed demo broadcast scripts if none exist
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        count = (await session.execute(select(func.count()).select_from(BroadcastScriptRow))).scalar()
        if count == 0:
            import json
            demo_scripts = [
                BroadcastScriptRow(
                    id="demo001",
                    headline="AI Breakthrough: New Language Model Achieves Human-Level Reasoning",
                    english_script="In a groundbreaking development, researchers have unveiled a new artificial intelligence system capable of complex reasoning tasks previously thought to be exclusively human. The model, trained on diverse datasets, demonstrates remarkable abilities in mathematics, coding, and scientific analysis. Experts say this could revolutionize industries from healthcare to finance, while raising important questions about AI safety and governance.",
                    hindi_script="एक अभूतपूर्व विकास में, शोधकर्ताओं ने एक नई कृत्रिम बुद्धिमत्ता प्रणाली का अनावरण किया है जो जटिल तर्क कार्यों में सक्षम है। यह मॉडल गणित, कोडिंग और वैज्ञानिक विश्लेषण में उल्लेखनीय क्षमताएं प्रदर्शित करता है।",
                    translations_json="{}",
                    category="technology",
                    source_url="https://example.com/ai-breakthrough",
                    word_count_en=73,
                    word_count_hi=38,
                    estimated_duration_seconds=29,
                    created_at=datetime.utcnow(),
                ),
                BroadcastScriptRow(
                    id="demo002",
                    headline="Global Markets Rally as Central Banks Signal Rate Cuts",
                    english_script="Stock markets around the world surged today as major central banks signaled a coordinated shift toward monetary easing. The Federal Reserve, European Central Bank, and Bank of England all indicated that interest rate reductions are on the horizon, citing cooling inflation and stable employment figures. The S&P 500 jumped 2.3 percent while European indices posted their strongest gains in months.",
                    hindi_script="आज दुनिया भर के शेयर बाजारों में तेजी आई क्योंकि प्रमुख केंद्रीय बैंकों ने मौद्रिक नरमी की ओर संकेत दिया। फेडरल रिजर्व और यूरोपीय सेंट्रल बैंक ने ब्याज दरों में कटौती का संकेत दिया।",
                    translations_json="{}",
                    category="finance",
                    source_url="https://example.com/markets-rally",
                    word_count_en=62,
                    word_count_hi=35,
                    estimated_duration_seconds=25,
                    created_at=datetime.utcnow(),
                ),
                BroadcastScriptRow(
                    id="demo003",
                    headline="Climate Summit Reaches Historic Agreement on Carbon Emissions",
                    english_script="World leaders at the Global Climate Summit have reached a landmark agreement to reduce carbon emissions by 60 percent by 2035. The deal, signed by 195 nations, includes binding commitments for renewable energy investment, phasing out coal power plants, and establishing a 100 billion dollar green transition fund for developing nations. Environmental groups have cautiously welcomed the agreement while pushing for faster implementation timelines.",
                    hindi_script="वैश्विक जलवायु शिखर सम्मेलन में विश्व नेताओं ने 2035 तक कार्बन उत्सर्जन में 60 प्रतिशत कटौती के लिए एक ऐतिहासिक समझौता किया है। इस समझौते पर 195 देशों ने हस्ताक्षर किए हैं।",
                    translations_json="{}",
                    category="science",
                    source_url="https://example.com/climate-summit",
                    word_count_en=68,
                    word_count_hi=34,
                    estimated_duration_seconds=27,
                    created_at=datetime.utcnow(),
                ),
                BroadcastScriptRow(
                    id="demo004",
                    headline="India's Space Agency Successfully Launches Mars Sample Return Mission",
                    english_script="ISRO has achieved another milestone in space exploration with the successful launch of its Mars Sample Return mission. The spacecraft, carrying advanced robotic systems, is expected to reach Mars orbit within nine months and collect soil samples from the Jezero Crater region. This mission positions India as the fourth nation capable of interplanetary sample return, following the United States, China, and Japan.",
                    hindi_script="इसरो ने मंगल नमूना वापसी मिशन के सफल प्रक्षेपण के साथ अंतरिक्ष अन्वेषण में एक और मील का पत्थर हासिल किया है। अंतरिक्ष यान नौ महीने में मंगल की कक्षा में पहुंचने की उम्मीद है।",
                    translations_json="{}",
                    category="science",
                    source_url="https://example.com/isro-mars",
                    word_count_en=67,
                    word_count_hi=32,
                    estimated_duration_seconds=27,
                    created_at=datetime.utcnow(),
                ),
                BroadcastScriptRow(
                    id="demo005",
                    headline="Cybersecurity Alert: Major Data Breach Affects 50 Million Users",
                    english_script="A massive cybersecurity breach has exposed the personal data of approximately 50 million users across a popular social media platform. Security researchers discovered the vulnerability in the platform's authentication system, which allowed unauthorized access to user profiles, email addresses, and encrypted passwords. The company has initiated a mandatory password reset and is working with law enforcement agencies to investigate the incident.",
                    hindi_script="एक बड़े साइबर सुरक्षा उल्लंघन ने एक लोकप्रिय सोशल मीडिया प्लेटफॉर्म पर लगभग 5 करोड़ उपयोगकर्ताओं के व्यक्तिगत डेटा को उजागर कर दिया है। कंपनी ने अनिवार्य पासवर्ड रीसेट शुरू कर दिया है।",
                    translations_json="{}",
                    category="technology",
                    source_url="https://example.com/data-breach",
                    word_count_en=64,
                    word_count_hi=30,
                    estimated_duration_seconds=26,
                    created_at=datetime.utcnow(),
                ),
            ]
            session.add_all(demo_scripts)
            await session.commit()


async def check_db_health() -> dict:
    """Verify the live database connection with a lightweight SELECT 1."""
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "driver": engine.url.drivername}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def save_script_to_db(script_data: dict):
    """Persist a BroadcastScript to the database."""
    import json
    async with AsyncSessionLocal() as session:
        row = BroadcastScriptRow(
            id=script_data["id"],
            headline=script_data["headline"],
            english_script=script_data["english_script"],
            hindi_script=script_data.get("hindi_script", ""),
            translations_json=json.dumps(script_data.get("translations", {})),
            category=script_data.get("category", "general"),
            source_url=script_data.get("source_url", ""),
            word_count_en=script_data.get("word_count_en", 0),
            word_count_hi=script_data.get("word_count_hi", 0),
            estimated_duration_seconds=script_data.get("estimated_duration_seconds", 0),
            created_at=script_data.get("created_at", datetime.utcnow()),
        )
        await session.merge(row)
        await session.commit()


async def load_all_scripts() -> list[dict]:
    """Load all scripts from the database, newest first."""
    import json
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BroadcastScriptRow).order_by(BroadcastScriptRow.created_at.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "headline": r.headline,
                "english_script": r.english_script,
                "hindi_script": r.hindi_script,
                "translations": json.loads(r.translations_json) if r.translations_json else {},
                "category": r.category,
                "source_url": r.source_url,
                "word_count_en": r.word_count_en,
                "word_count_hi": r.word_count_hi,
                "estimated_duration_seconds": r.estimated_duration_seconds,
                "created_at": r.created_at,
            }
            for r in rows
        ]


async def record_agent_metric(agent_name: str, status: str, latency_seconds: float):
    async with AsyncSessionLocal() as session:
        session.add(AgentMetricRow(
            agent_name=agent_name, status=status, latency_seconds=latency_seconds,
        ))
        await session.commit()


async def get_agent_stats() -> list[dict]:
    from sqlalchemy import select, func
    async with AsyncSessionLocal() as session:
        stmt = (
            select(
                AgentMetricRow.agent_name,
                func.count().label("total"),
                func.sum(AgentMetricRow.tasks_completed).label("tasks_completed"),
                func.avg(AgentMetricRow.latency_seconds).label("avg_latency"),
            )
            .group_by(AgentMetricRow.agent_name)
        )
        result = await session.execute(stmt)
        rows = result.all()

        latest_stmt = select(AgentMetricRow).order_by(AgentMetricRow.created_at.desc()).limit(50)
        latest_result = await session.execute(latest_stmt)
        latest = {r.agent_name: r for r in latest_result.scalars().all()}

        return [
            {
                "name": r.agent_name,
                "tasks_completed": r.tasks_completed or 0,
                "avg_latency": f"{r.avg_latency:.1f}s" if r.avg_latency else "--",
                "status": latest[r.agent_name].status if r.agent_name in latest else "idle",
                "last_run": latest[r.agent_name].created_at.strftime("%H:%M:%S") if r.agent_name in latest else "--",
            }
            for r in rows
        ]


async def get_throughput_stats() -> dict:
    from sqlalchemy import select, func, extract
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        day_ago = now - timedelta(hours=24)

        total_stmt = select(func.count()).select_from(BroadcastScriptRow).where(
            BroadcastScriptRow.created_at >= day_ago
        )
        total_today = (await session.execute(total_stmt)).scalar() or 0

        hourly = []
        for i in range(23, -1, -1):
            hour_start = now - timedelta(hours=i + 1)
            hour_end = now - timedelta(hours=i)
            count_stmt = select(func.count()).select_from(BroadcastScriptRow).where(
                BroadcastScriptRow.created_at >= hour_start,
                BroadcastScriptRow.created_at < hour_end,
            )
            count = (await session.execute(count_stmt)).scalar() or 0
            hourly.append({"hour": hour_end.strftime("%H:00"), "articles": count})

        cat_stmt = (
            select(BroadcastScriptRow.category, func.count().label("count"))
            .where(BroadcastScriptRow.created_at >= day_ago)
            .group_by(BroadcastScriptRow.category)
            .order_by(func.count().desc())
            .limit(6)
        )
        cat_result = await session.execute(cat_stmt)
        categories = [{"category": r.category, "count": r.count} for r in cat_result.all()]

        return {
            "total_today": total_today,
            "avg_per_hour": round(total_today / 24, 1),
            "hourly": hourly,
            "categories": categories,
        }


async def get_revenue_stats() -> dict:
    from sqlalchemy import select, func
    async with AsyncSessionLocal() as session:
        total_clients = (await session.execute(
            select(func.count()).select_from(ClientAPIKey).where(ClientAPIKey.is_active == True)
        )).scalar() or 0

        total_requests = (await session.execute(
            select(func.sum(ClientAPIKey.requests_used)).select_from(ClientAPIKey)
        )).scalar() or 0

        clients = (await session.execute(
            select(ClientAPIKey).where(ClientAPIKey.is_active == True)
        )).scalars().all()

        tier_breakdown = {}
        for c in clients:
            tier_breakdown[c.plan_tier] = tier_breakdown.get(c.plan_tier, 0) + 1

        return {
            "total_clients": total_clients,
            "total_api_requests": total_requests or 0,
            "tier_breakdown": tier_breakdown,
            "clients": [
                {
                    "name": c.client_name,
                    "tier": c.plan_tier,
                    "requests_used": c.requests_used,
                    "monthly_quota": c.monthly_quota,
                }
                for c in clients
            ],
        }


async def save_media_job(job_data: dict):
    async with AsyncSessionLocal() as session:
        row = MediaJobRow(**job_data)
        await session.merge(row)
        await session.commit()


async def update_media_job(job_id: str, **kwargs):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MediaJobRow).where(MediaJobRow.id == job_id))
        row = result.scalars().first()
        if row:
            for k, v in kwargs.items():
                setattr(row, k, v)
            await session.commit()


async def get_media_jobs(limit: int = 20) -> list[dict]:
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MediaJobRow).order_by(MediaJobRow.created_at.desc()).limit(limit)
        )
        return [
            {
                "id": r.id, "script_id": r.script_id, "headline": r.headline,
                "media_type": r.media_type, "language": r.language,
                "status": r.status, "progress": r.progress,
                "duration": r.duration, "output_url": r.output_url,
                "created_at": r.created_at.isoformat(),
            }
            for r in result.scalars().all()
        ]
