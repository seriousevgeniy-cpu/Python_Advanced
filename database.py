"""
Асинхронное подключение к БД. В отличие от примера из материалов урока
(один общий на всё приложение объект Session), здесь для каждого запроса
создаётся своя сессия через FastAPI Depends -- один AsyncSession нельзя
безопасно использовать из нескольких конкурентных запросов одновременно.
"""

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL: str = "sqlite+aiosqlite:///./cookbook.db"

engine = create_async_engine(DATABASE_URL, echo=False)

# expire_on_commit=False, чтобы после commit можно было читать атрибуты
# созданного объекта без дополнительного похода в БД (нужно для ответа
# на POST /recipes сразу после создания записи).
async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def init_models() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
