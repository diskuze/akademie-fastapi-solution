from typing import Any
from typing import Iterable
from typing import List
from typing import Optional

import strawberry
from sqlalchemy import exists
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from diskuze.dependencies.context import AppContext
from diskuze import models


# TODO: based on the models, define schema object types

# TODO: naming models / objects?
@strawberry.type
class Discussion:
    id: int
    canonical: str

    # TODO: add comments listing


@strawberry.type
class User:
    id: int
    name: str


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

        comment, = await info.context.data_loader.comment.load([self.reply_to_id])
        return comment

    @strawberry.field
    async def replies(self, info: Info[AppContext, Any]) -> List["Comment"]:
        comments = info.context.data_loader.comment_replies.load([self.id])
        return [Comment.from_model(comment) for comment in comments]

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
    async def comments(self, info: Info[AppContext, Any], first: int = 10, offset: int = 0) -> List[Comment]:
        async with info.context.db.session() as session:
            query = select(models.Comment).limit(first).offset(offset)
            result = await session.execute(query)
            comments: Iterable[models.Comment] = result.scalars()

        return [Comment.from_model(comment) for comment in comments]


@strawberry.input
class CommentInput:
    content: str
    discussion_canonical: str
    reply_to: Optional[int] = None


@strawberry.type
class Mutation:
    # TODO: to implement
    @strawberry.mutation
    async def create_comment(
            self,
            info: Info[AppContext, Any],
            input_: strawberry.arguments.Annotated[CommentInput, strawberry.argument(name="input")],
    ) -> Optional[Comment]:  # TODO: return status, too
        if not info.context.user:
            return None

        if not input_.content:
            return None

        session: AsyncSession  # TODO: fix typing of the context manager
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
