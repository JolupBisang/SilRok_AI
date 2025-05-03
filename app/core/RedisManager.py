import asyncio
from redis.asyncio import Redis

from ServerObject import ServerObject
from .config import settings


class RedisManager(ServerObject):
    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        ttl: int,
        decode_responses: bool,
        max_memory: str,
        max_memory_policy: str,
        list_ttl: int = settings.REDIS_LIST_TTL,
    ):
        if self.__class__ is RedisManager:
            raise TypeError("Cannot instantiate abstract class RedisManager directly")

        super().__init__()
        self.__TTL = ttl
        self.__LIST_TTL = list_ttl
        self.__redis = Redis(
            host=host, port=port, db=db, decode_responses=decode_responses
        )

        asyncio.create_task(self.__configure(max_memory, max_memory_policy))

    async def __configure(self, max_memory: str, max_memory_policy: str):
        await self.__redis.config_set("maxmemory", max_memory)
        await self.__redis.config_set("maxmemory-policy", max_memory_policy)

    async def get(self, key: str):
        return await self.__redis.get(key)

    async def set(self, key: str, value, ttl: int = None):
        if ttl is None:
            ttl = self.__TTL
        await self.__redis.set(key, value, ex=ttl)

    async def delete(self, key: str):
        await self.__redis.delete(key)

    async def close(self):
        self.__redis.close()

    async def pop(self, key: str):
        return await self.__redis.eval(
            """
            local val = redis.call('GET', KEYS[1])
            if val then
                redis.call('DEL', KEYS[1])
            end
            return val
            """,
            1,
            key,
        )

    async def append_list(self, key: str, value, ttl: int = None):
        if ttl is None:
            ttl = self.__LIST_TTL
        await self.__redis.rpush(key, value)
        await self.__redis.expire(key, self.__LIST_TTL)

    async def pop_list(self, key: str):
        return await self.__redis.eval(
            """
            local vals = redis.call('LRANGE', KEYS[1], 0, -1)
            if #vals > 0 then
                redis.call('DEL', KEYS[1])
            end
            return vals
            """,
            1,
            key,
        )
