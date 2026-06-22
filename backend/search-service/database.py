"""
Search index storage — full-text search over broadcast scripts.
"""

import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime

from config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

if not DATABASE_URL:
    DB_PATH = os.path.join(os.path.dirname(__file__), "search_index.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class SearchEntry(Base):
    __tablename__ = "search_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    headline: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String, index=True, default="general")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
