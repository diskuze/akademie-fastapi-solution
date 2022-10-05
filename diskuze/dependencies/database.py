from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from diskuze.dependencies.config import Config
from diskuze.dependencies.config import get_config


class Database:
    def __init__(self, connection_url: str):
        self.engine = create_async_engine(connection_url)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


def get_database(config: Config = Depends(get_config)):
    return Database(
        f"mysql+aiomysql://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}/{config.DB_NAME}"
    )
