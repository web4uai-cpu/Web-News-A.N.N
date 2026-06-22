"""
Database models and session management for the Auth Service.
Manages B2B client API keys and quotas.
"""

import os
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime

from config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

if not DATABASE_URL:
    DB_PATH = os.path.join(os.path.dirname(__file__), "auth_service.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine_kwargs = {"echo": False}
if "postgresql" in DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


class ClientAPIKey(Base):
    __tablename__ = "client_api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_name: Mapped[str] = mapped_column(String, index=True)
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    plan_tier: Mapped[str] = mapped_column(String, default="standard")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    monthly_quota: Mapped[int] = mapped_column(Integer, default=1000)
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
    webhook_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ClientAPIKey).where(ClientAPIKey.api_key == "ann_demo_key_777")
        )
        if not result.scalars().first():
            demo = ClientAPIKey(
                client_name="Demo Developer Client",
                api_key="ann_demo_key_777",
                plan_tier="enterprise",
                monthly_quota=50000,
            )
            session.add(demo)
            await session.commit()
