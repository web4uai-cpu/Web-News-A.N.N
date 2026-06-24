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
    await _seed_demo_data()


async def _seed_demo_data():
    from sqlalchemy import select, func
    async with AsyncSessionLocal() as session:
        count = (await session.execute(select(func.count()).select_from(ScriptRow))).scalar()
        if count:
            return
        demos = [
            ScriptRow(
                id="demo001",
                headline="AI Breakthrough: New Language Model Achieves Human-Level Reasoning",
                english_script="In a groundbreaking development, researchers have unveiled a new artificial intelligence system capable of complex reasoning tasks previously thought to be exclusively human. The model demonstrates remarkable abilities in mathematics, coding, and scientific analysis. Experts say this could revolutionize industries from healthcare to finance.",
                hindi_script="एक अभूतपूर्व विकास में, शोधकर्ताओं ने एक नई कृत्रिम बुद्धिमत्ता प्रणाली का अनावरण किया है जो जटिल तर्क कार्यों में सक्षम है।",
                category="technology",
                source_url="https://example.com/ai-breakthrough",
                word_count_en=73, word_count_hi=38, estimated_duration_seconds=29,
            ),
            ScriptRow(
                id="demo002",
                headline="Global Markets Rally as Central Banks Signal Rate Cuts",
                english_script="Stock markets around the world surged today as major central banks signaled a coordinated shift toward monetary easing. The Federal Reserve, European Central Bank, and Bank of England all indicated that interest rate reductions are on the horizon, citing cooling inflation and stable employment figures.",
                hindi_script="आज दुनिया भर के शेयर बाजारों में तेजी आई क्योंकि प्रमुख केंद्रीय बैंकों ने मौद्रिक नरमी की ओर संकेत दिया।",
                category="finance",
                source_url="https://example.com/markets-rally",
                word_count_en=62, word_count_hi=35, estimated_duration_seconds=25,
            ),
            ScriptRow(
                id="demo003",
                headline="Climate Summit Reaches Historic Agreement on Carbon Emissions",
                english_script="World leaders at the Global Climate Summit have reached a landmark agreement to reduce carbon emissions by 60 percent by 2035. The deal, signed by 195 nations, includes binding commitments for renewable energy investment and establishing a 100 billion dollar green transition fund for developing nations.",
                hindi_script="वैश्विक जलवायु शिखर सम्मेलन में विश्व नेताओं ने 2035 तक कार्बन उत्सर्जन में 60 प्रतिशत कटौती के लिए एक ऐतिहासिक समझौता किया है।",
                category="science",
                source_url="https://example.com/climate-summit",
                word_count_en=68, word_count_hi=34, estimated_duration_seconds=27,
            ),
            ScriptRow(
                id="demo004",
                headline="India's Space Agency Successfully Launches Mars Sample Return Mission",
                english_script="ISRO has achieved another milestone in space exploration with the successful launch of its Mars Sample Return mission. The spacecraft is expected to reach Mars orbit within nine months and collect soil samples from the Jezero Crater region, positioning India as the fourth nation capable of interplanetary sample return.",
                hindi_script="इसरो ने मंगल नमूना वापसी मिशन के सफल प्रक्षेपण के साथ अंतरिक्ष अन्वेषण में एक और मील का पत्थर हासिल किया है।",
                category="science",
                source_url="https://example.com/isro-mars",
                word_count_en=67, word_count_hi=32, estimated_duration_seconds=27,
            ),
            ScriptRow(
                id="demo005",
                headline="Cybersecurity Alert: Major Data Breach Affects 50 Million Users",
                english_script="A massive cybersecurity breach has exposed the personal data of approximately 50 million users across a popular social media platform. Security researchers discovered the vulnerability in the platform's authentication system. The company has initiated a mandatory password reset and is working with law enforcement.",
                hindi_script="एक बड़े साइबर सुरक्षा उल्लंघन ने एक लोकप्रिय सोशल मीडिया प्लेटफॉर्म पर लगभग 5 करोड़ उपयोगकर्ताओं के व्यक्तिगत डेटा को उजागर कर दिया है।",
                category="technology",
                source_url="https://example.com/data-breach",
                word_count_en=64, word_count_hi=30, estimated_duration_seconds=26,
            ),
        ]
        session.add_all(demos)
        await session.commit()
