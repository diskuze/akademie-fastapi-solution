from typing import List
from typing import Type
from typing import TypeVar

from fastapi import Depends
from sqlalchemy import select

from diskuze.models import User
from diskuze.dependencies.database import Database
from diskuze.dependencies.database import get_database
from diskuze.models import Base
from diskuze.models import Comment
from diskuze.models import Discussion

T = TypeVar("T", bound=Base)


class DatabaseIdentityDataLoader:
    def __init__(self, db: Database, model: Type[T]):
        self.db = db
        self.model = model

    async def load(self, ids: List[int]) -> List[T]:
        # TODO: to implement
        async with self.db.session() as session:
            query = select(self.model).where(self.model.id.in_(ids))
            result = await session.execute(query)
            items = list(result.scalars())

        return items


# TODO: design a solution for comment replies data loader
class CommentRepliesDataLoader:
    def __init__(self, db: Database):
        self.db = db

    async def load(self, ids: List[int]) -> List[Comment]:
        async with self.db.session() as session:
            query = select(Comment).where(Comment.reply_to_id.in_(ids))
            result = await session.execute(query)
            items = list(result.scalars())

        return items


class DataLoaderRegistry:
    def __init__(self, db: Database = Depends(get_database)):
        self.comment = DatabaseIdentityDataLoader(db, Comment)
        self.comment_replies = CommentRepliesDataLoader(db)
        self.discussion = DatabaseIdentityDataLoader(db, Discussion)
        self.user = DatabaseIdentityDataLoader(db, User)
