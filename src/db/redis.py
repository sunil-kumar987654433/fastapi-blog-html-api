import redis.asyncio as aioredis
from src.config import Config

JTI_EXPIRY = 3600


redis_client = aioredis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    decode_responses=True,
    db=0,
    socket_connect_timeout=5,
    retry_on_timeout=True
)


async def add_jti_to_blocklist(jti: str)->None:
    print("add_jti_to_blocklist   jti---", jti)
    await redis_client.set(
        name=jti,
        value='revoked',
    )


async def token_in_blocklist(jti: str)->bool:
    return await redis_client.get(name=jti)
  