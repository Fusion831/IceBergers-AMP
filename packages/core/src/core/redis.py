"""Redis Connection and In-Memory Fallback Cache."""
import json
from typing import Any, Optional
from core.config import settings
from core.logging import get_logger

logger = get_logger("core.redis")

_redis_client = None


class InMemoryCache:
    """Fallback in-memory key-value cache when Redis is disabled or offline."""
    def __init__(self):
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._store[key] = str(value)
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    async def exists(self, key: str) -> bool:
        return key in self._store


_in_memory_cache = InMemoryCache()


async def get_redis_client():
    """Returns async Redis client or in-memory fallback if Redis is not reachable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        # Test connection
        await client.ping()
        _redis_client = client
        logger.info("Connected to Redis server successfully", url=settings.REDIS_URL)
        return _redis_client
    except Exception as exc:
        logger.warning(
            "Redis connection unavailable; operating with in-memory cache fallback",
            error=str(exc)
        )
        return _in_memory_cache
