from typing import Any
from typing import List
from typing import Optional

import strawberry
from sqlalchemy import exists
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from strawberry.types import Info

from diskuze.dependencies.context import AppContext
from diskuze import models


@strawberry.type
class Discussion:
    id: int
    canonical: str

    @strawberry.field(description="Comments in discussion listing")
    async def comments(self, info: Info[AppContext, Any], first: int = 10, offset: int = 0) -> List["Comment"]:
        async with info.context.db.session() as session:
            query = select(models.Comment).where(models.Comment.discussion_id == self.id).limit(first).offset(offset)
            result = await session.execute(query)
            comments = result.scalars().all()

        return [Comment.from_model(comment) for comment in comments]


@strawberry.type
class User:
    id: int
    nick: str

    @strawberry.field
    async def name(self, info: Info[AppContext, Any]) -> Optional[str]:
        name = await info.context.data_loader.user_full_name.load(self.id)
        return name


@strawberry.type
class Comment:
    @staticmethod
    def from_model(comment: models.Comment) -> "Comment":
        return Comment(
            id=comment.id,
            content=comment.content,
            reply_to_id=comment.reply_to_id,
            discussion_id=comment.discussion_id,
            user_id=comment.user_id,
        )

    id: int
    content: str

    reply_to_id: strawberry.Private[int]
    discussion_id: strawberry.Private[int]
    user_id: strawberry.Private[int]

    @strawberry.field
    async def reply_to(self, info: Info[AppContext, Any]) -> Optional["Comment"]:
        if not self.reply_to_id:
            return None

        comment = await info.context.data_loader.comment.load(self.reply_to_id)
        return Comment.from_model(comment)

    @strawberry.field
    async def replies(self, info: Info[AppContext, Any], first: int = 10, offset: int = 0) -> List["Comment"]:
        async with info.context.db.session() as session:
            query = (
                select(models.Comment)
                .where(models.Comment.reply_to_id == self.id)
                .limit(first)
                .offset(offset)
            )
            result = await session.execute(query)
            comments = result.scalars().all()

        return [Comment.from_model(comment) for comment in comments]

        # # Data loader solution is quite limiting as it cannot accept given arguments
        # comment_ids = await info.context.data_loader.comment_replies.load(self.id)
        # comments = await info.context.data_loader.comment.load_many(comment_ids)
        # return [Comment.from_model(comment) for comment in comments]

    @strawberry.field
    async def discussion(self, info: Info[AppContext, Any]) -> Discussion:
        discussion = await info.context.data_loader.discussion.load(self.discussion_id)
        return discussion

    @strawberry.field
    async def user(self, info: Info[AppContext, Any]) -> User:
        user = await info.context.data_loader.user.load(self.user_id)
        return user


@strawberry.type
class Query:
    @strawberry.field(description="Says \"Hello World!\"")
    def hello(self) -> str:
        return "Hello World!"

    @strawberry.field(description="Gives boring statistics about comments total")
    async def total(self, info: Info[AppContext, Any]) -> int:
        async with info.context.db.session() as session:
            query = select(count()).select_from(models.Comment)
            result = await session.execute(query)
            total = result.scalar()

        return total

    @strawberry.field(description="All comments listing")
    async def comments(self, info: Info[AppContext, Any], first: int = 10, offset: int = 0) -> List[Comment]:
        async with info.context.db.session() as session:
            query = select(models.Comment).limit(first).offset(offset)
            result = await session.execute(query)
            comments = result.scalars().all()

        return [Comment.from_model(comment) for comment in comments]

    @strawberry.field(description="Discussion obtained by its canonical identifier")
    async def discussion(self, info: Info[AppContext, Any], canonical: str) -> Optional[Discussion]:
        async with info.context.db.session() as session:
            query = select(models.Discussion).where(models.Discussion.canonical == canonical)
            result = await session.execute(query)
            discussion = result.scalar_one_or_none()

        return discussion


@strawberry.input
class CommentInput:
    content: str
    discussion_canonical: str
    reply_to: Optional[int] = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_comment(
            self,
            info: Info[AppContext, Any],
            input_: strawberry.arguments.Annotated[CommentInput, strawberry.argument(name="input")],
    ) -> Optional[Comment]:
        if not info.context.user:
            return None

        if not input_.content:
            return None

        async with info.context.db.session() as session:
            query = select(models.Discussion.id).where(models.Discussion.canonical == input_.discussion_canonical)
            result = await session.execute(query)
            discussion_id = result.scalar_one_or_none()

            if not discussion_id:
                return None

            if input_.reply_to:
                query = select(exists(select(models.Comment).where(models.Comment.id == input_.reply_to)))
                result = await session.execute(query)
                reply_exists = result.scalar()

                if not reply_exists:
                    return None

            comment = models.Comment(content=input_.content, discussion_id=discussion_id, user_id=info.context.user.id)
            session.add(comment)

        return comment


schema = strawberry.Schema(Query, Mutation)
