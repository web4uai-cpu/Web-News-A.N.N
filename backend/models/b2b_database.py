"""
A.N.N. B2B Database Module
Using SQLAlchemy + aiosqlite for high-performance, async API Key management.
Tracks enterprise clients, their monthly billing cycles, and API quotas.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ann_enterprise.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    # Upgrade standard Postgres connection strings to asyncpg for FastAPI non-blocking speed
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

class ClientAPIKey(Base):
    """
    Represents an Enterprise B2B Client paying for news feed access.
    """
    __tablename__ = "client_api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_name: Mapped[str] = mapped_column(String, index=True)
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    plan_tier: Mapped[str] = mapped_column(String, default="standard")  # e.g. "free", "standard", "enterprise"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Quota Limits (Requests allowed per billing cycle)
    monthly_quota: Mapped[int] = mapped_column(Integer, default=1000)
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Billing/Webhook Settings
    webhook_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    """Create the SQLite tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed a demo key for the developer to test with immediately
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(ClientAPIKey).where(ClientAPIKey.api_key == "ann_demo_key_777"))
        if not result.scalars().first():
            demo_client = ClientAPIKey(
                client_name="Demo Developer Client",
                api_key="ann_demo_key_777",
                plan_tier="enterprise",
                monthly_quota=50000,
            )
            session.add(demo_client)
            await session.commit()
