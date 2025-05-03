from .config import settings
from .RedisManager import RedisManager


class RedisByteManager(RedisManager):
    def __init__(
        self,
        host: str = settings.REDIS_BYTE_HOST,
        port: int = settings.REDIS_BYTE_PORT,
        db: int = settings.REDIS_BYTE_DB,
        ttl: int = settings.REDIS_BYTE_TTL,
        decode_responses: bool = settings.REDIS_BYTE_DECODE_RESPONSES,
        max_memory: str = settings.REDIS_BYTE_MAX_MEMORY,
        max_memory_policy: str = settings.REDIS_STR_MAX_MEMORY_POLICY,
    ):
        super().__init__(
            host=host,
            port=port,
            db=db,
            ttl=ttl,
            decode_responses=decode_responses,
            max_memory=max_memory,
            max_memory_policy=max_memory_policy,
        )
