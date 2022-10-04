from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

from fastapi import Depends
from fastapi import Request
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from strawberry.fastapi import BaseContext

from diskuze import models
from diskuze.models import Base


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


def get_database() -> Database:
    return Database("mysql+aiomysql://root:root@127.0.0.1/diskuze")


async def get_auth_user(request: Request, db: Database = Depends(get_database)) -> Optional[models.User]:
    authorization = (request.headers.get("Authorization") or "").split(" ", 1)
    if len(authorization) < 2:
        return None  # unauthorized or invalid format

    auth_type, username = authorization
    if auth_type != "User" or not username:
        return None  # invalid type or empty username

    async with db.session() as session:
        query = select(models.User).where(models.User.name == username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

    return user

T = TypeVar("T", bound=Base)


class DatabaseDataLoader:
    def __init__(self, db: Database, model: Type[T]):
        self.db = db
        self.model = model

    async def load(self, ids: List[int]) -> List[T]:
        async with self.db.session() as session:
            query = select(self.model).where(self.model.id.in_(ids))
            result = await session.execute(query)
            items = list(result.scalars())

        return items


class DataLoaderRegistry:
    def __init__(self, db: Database = Depends(get_database)):
        self.comment = DatabaseDataLoader(db, models.Comment)
        self.discussion = DatabaseDataLoader(db, models.Discussion)
        self.user = DatabaseDataLoader(db, models.User)


class AppContext(BaseContext):
    def __init__(
        self,
        db: Database = Depends(get_database),
        data_loader: DataLoaderRegistry = Depends(DataLoaderRegistry),
        user: Optional[models.User] = Depends(get_auth_user),
    ):
        super().__init__()
        self.db = db
        self.data_loader = data_loader
        self.user = user

