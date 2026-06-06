from redis.asyncio import Redis

from app.database.config import config


_redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    username=config.REDIS_USER,
    password=config.REDIS_PASSWORD,
    decode_responses=True,
)


async def add_jti_to_blacklist(jti: str, ex: int):
    await _redis_client.set(jti, "blacklisted", ex=ex)


async def is_jti_blacklisted(jti: str):
    return await _redis_client.exists(jti)
