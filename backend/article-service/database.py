"""
Article storage — persistent script storage replacing in-memory dict.
"""

import os
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, JSON

from config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

if not DATABASE_URL:
    DB_PATH = os.path.join(os.path.dirname(__file__), "articles.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine_kwargs = {"echo": False}
if "postgresql" in DATABASE_URL:
    engine_kwargs.update({"pool_size": 20, "max_overflow": 10, "pool_timeout": 30, "pool_recycle": 1800})

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class ScriptRow(Base):
    __tablename__ = "broadcast_scripts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    headline: Mapped[str] = mapped_column(String, index=True)
    english_script: Mapped[str] = mapped_column(Text)
    hindi_script: Mapped[str] = mapped_column(Text, default="")
    translations: Mapped[dict] = mapped_column(JSON, default=dict)
    category: Mapped[str] = mapped_column(String, index=True, default="general")
    source_url: Mapped[str] = mapped_column(String, default="")
    word_count_en: Mapped[int] = mapped_column(Integer, default=0)
    word_count_hi: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
