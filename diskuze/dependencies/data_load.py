import asyncio
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

import httpx
from fastapi import Depends
from httpx import Response
from sqlalchemy import select
from strawberry.dataloader import DataLoader

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
            items = result.scalars().all()  # TODO: use iterators or lists? efficiency vs debug-ability

        return items


# TODO: design a solution for comment replies data loader
class CommentRepliesDataLoader:
    def __init__(self, db: Database):
        self.db = db

    async def load(self, ids: List[int]) -> List[List[int]]:
        async with self.db.session() as session:
            query = select(Comment.id, Comment.reply_to_id).where(Comment.reply_to_id.in_(ids))
            result = await session.execute(query)
            reply_edges = result.all()

        reply_mapping: Dict[int, List[int]] = {}

        for (id_, reply_to_id) in reply_edges:
            reply_mapping.setdefault(reply_to_id, []).append(id_)

        return [reply_mapping.get(id_, []) for id_ in ids]


# TODO: to implement
async def load_full_name(ids: List[int]) -> List[Optional[str]]:
    """
    https://github.com/encode/httpx
    https://randomuser.me/documentation
    """

    # TODO: truly async with only 1 client?
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            *(client.get(f"https://randomuser.me/api/?seed={id_}") for id_ in ids)
        )

    def _compose_full_name(response: Response):
        if response.status_code != 200:
            return None

        name = response.json()["results"][0]["name"]
        first, last = name["first"], name["last"]
        return f"{first} {last}"

    return [_compose_full_name(response) for response in responses]


class DataLoaderRegistry:
    def __init__(self, db: Database = Depends(get_database)):
        self.comment = DataLoader(load_fn=DatabaseIdentityDataLoader(db, Comment).load)
        self.comment_replies = DataLoader(load_fn=CommentRepliesDataLoader(db).load)
        self.discussion = DataLoader(load_fn=DatabaseIdentityDataLoader(db, Discussion).load)
        self.user = DataLoader(load_fn=DatabaseIdentityDataLoader(db, User).load)
        self.user_full_name = DataLoader(load_fn=load_full_name)
