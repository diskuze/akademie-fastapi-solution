from typing import Any
from typing import List
from typing import Optional

import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from diskuze import AppContext
from diskuze import models


@strawberry.type
class Discussion:
    id: int
    canonical: str


@strawberry.type
class User:
    id: int
    name: str


@strawberry.type
class Comment:
    id: int
    content: str

    discussion_id: strawberry.Private[int]
    user_id: strawberry.Private[int]

    @strawberry.field
    async def discussion(self, info: Info[AppContext, Any]) -> Discussion:
        discussion, = await info.context.data_loader.discussion.load([self.discussion_id])
        return discussion

    @strawberry.field
    async def user(self, info: Info[AppContext, Any]) -> User:
        user, = await info.context.data_loader.user.load([self.user_id])
        return user


@strawberry.type
class Query:
    @strawberry.field(description="Says \"Hello World!\"")
    def hello(self) -> str:
        return "Hello World!"

    @strawberry.field(description="All comments")
    async def comments(self, info: Info[AppContext, None], first: int = 10, offset: int = 0) -> List[Comment]:
        async with info.context.db.session() as session:
            query = select(models.Comment).limit(first).offset(offset)
            result = await session.execute(query)
            comments = result.scalars()

        return [
            Comment(
                id=comment.id,
                content=comment.content,
                discussion_id=comment.discussion_id,
                user_id=comment.user_id,
            )
            for comment in comments
        ]


@strawberry.input
class CommentInput:
    content: str
    discussion_canonical: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_comment(self, info: Info[AppContext, None], input: CommentInput) -> Optional[Comment]:
        if not info.context.user:
            return None

        if not input.content:
            return None

        session: AsyncSession  # TODO: fix typing of the context manager
        async with info.context.db.session() as session:
            query = select(models.Discussion.id).where(models.Discussion.canonical == input.discussion_canonical)
            result = await session.execute(query)
            discussion_id = result.scalar_one_or_none()

            if not discussion_id:
                return None

            comment = models.Comment(content=input.content, discussion_id=discussion_id, user_id=info.context.user.id)
            session.add(comment)

        return comment


schema = strawberry.Schema(Query, Mutation)
