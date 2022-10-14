from typing import Optional

from fastapi import Depends
from fastapi import Request
from sqlalchemy import select

from diskuze.models import User
from diskuze.dependencies.database import Database
from diskuze.dependencies.database import get_database


async def get_auth_user(request: Request, db: Database = Depends(get_database)) -> Optional[User]:
    """
    Gets currently authorized user based on Request headers and return that.
    Otherwise, return None.

    The header should come in the form of:
    Authorization: User <nick>
    """

    authorization = (request.headers.get("Authorization") or "").split(" ", 1)
    if len(authorization) < 2:
        return None  # unauthorized or invalid format

    auth_type, nick = authorization
    if auth_type != "User" or not nick:
        return None  # invalid type or empty nick

    async with db.session() as session:
        query = select(User).where(User.nick == nick)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

    return user
