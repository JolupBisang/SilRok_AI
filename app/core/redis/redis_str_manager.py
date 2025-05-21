from core import Settings

from .redis_manager import RedisManager


class RedisStrManager(RedisManager):
    def __init__(
        self,
        host: str = Settings.REDIS_STR_HOST,
        port: int = Settings.REDIS_STR_PORT,
        db: int = Settings.REDIS_STR_DB,
        ttl: int = Settings.REDIS_STR_TTL,
        decode_responses: bool = Settings.REDIS_STR_DECODE_RESPONSES,
        max_memory: str = Settings.REDIS_STR_MAX_MEMORY,
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

    async def pop(self, key: str) -> str:
        value = await super().pop(key)
        if value is None:
            return None
        return value.decode("utf-8")

    async def pop_list(self, key: str) -> list[str]:
        value = await super().pop(key)
        if value is None:
            return None
        return [v.decode("utf-8") for v in value]
