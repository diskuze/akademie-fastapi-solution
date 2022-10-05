from typing import Optional

from fastapi import Depends
from fastapi import Request
from sqlalchemy import select

from diskuze.models import User
from diskuze.dependencies.database import Database
from diskuze.dependencies.database import get_database


# TODO: to define
async def get_auth_user(request: Request, db: Database = Depends(get_database)) -> Optional[User]:
    authorization = (request.headers.get("Authorization") or "").split(" ", 1)
    if len(authorization) < 2:
        return None  # unauthorized or invalid format

    auth_type, username = authorization
    if auth_type != "User" or not username:
        return None  # invalid type or empty username

    async with db.session() as session:
        query = select(User).where(User.name == username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

    return user
