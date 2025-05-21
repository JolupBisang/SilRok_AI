from core import Settings

from .redis_manager import RedisManager


class RedisByteManager(RedisManager):
    def __init__(
        self,
        host: str = Settings.REDIS_BYTE_HOST,
        port: int = Settings.REDIS_BYTE_PORT,
        db: int = Settings.REDIS_BYTE_DB,
        ttl: int = Settings.REDIS_BYTE_TTL,
        decode_responses: bool = Settings.REDIS_BYTE_DECODE_RESPONSES,
        max_memory: str = Settings.REDIS_BYTE_MAX_MEMORY,
        max_memory_policy: str = Settings.REDIS_STR_MAX_MEMORY_POLICY,
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
