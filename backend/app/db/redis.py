from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings


class RedisClient:
    """Async Redis client wrapper with connection pool management."""

    def __init__(self):
        self._pool: aioredis.Redis | None = None

    async def initialize(self):
        self._pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )

    @property
    def pool(self) -> aioredis.Redis:
        if self._pool is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._pool

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    # Convenience methods for common operations
    async def get(self, key: str) -> str | None:
        return await self.pool.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        await self.pool.set(key, value, ex=ex)

    async def delete(self, key: str):
        await self.pool.delete(key)

    async def publish(self, channel: str, message: str):
        await self.pool.publish(channel, message)


redis_client = RedisClient()
