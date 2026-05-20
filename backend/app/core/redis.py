import redis.asyncio as aioredis

from app.config import settings

_redis_client = None


def _create_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1.5,
            )
        except Exception:
            _redis_client = False
    return _redis_client if _redis_client is not False else None


async def get_redis():
    global _redis_client
    if _redis_client is False:
        return None
    client = _create_redis()
    if client:
        try:
            await client.ping()
        except Exception:
            _redis_client = False
            return None
    return client
