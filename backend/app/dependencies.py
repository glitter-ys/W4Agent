from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.db.redis import redis_client, RedisClient


async def get_db(session: AsyncSession = Depends(get_async_session)) -> AsyncSession:
    yield session


async def get_redis() -> RedisClient:
    return redis_client
