
from src.config import Config
DATABASE_URL = Config.DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.db.base import Base
from typing import AsyncGenerator


engine = create_async_engine(
    url=DATABASE_URL,
    echo=True
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async_session = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False,
    class_=AsyncSession
    )

async def get_session()->AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session