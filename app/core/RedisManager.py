import asyncio
from redis.asyncio import Redis

from ServerObject import ServerObject

class RedisManager(ServerObject):
  def __init__(
    self, 
    host: str, 
    port: int, 
    db: int, 
    ttl: int,
    decode_responses: bool,
    max_memory: str,
    max_memory_policy: str
  ):
    if self.__class__ is RedisManager:
      raise TypeError("Cannot instantiate abstract class RedisManager directly")

    super().__init__()
    self.__TTL = ttl
    self.__redis = Redis(host=host, port=port, db=db, decode_responses=decode_responses)

    asyncio.create_task(self.__configure(max_memory, max_memory_policy))

  async def __configure(
    self, 
    max_memory: str, 
    max_memory_policy: str 
  ):
    await self.__redis.config_set("maxmemory", max_memory)
    await self.__redis.config_set("maxmemory-policy", max_memory_policy)

  async def get(self, key: str):
    return await self.__redis.get(key)

  async def set(self, key: str, value: str, ttl: int = None):
    if ttl is None:
      ttl = self.__TTL
    await self.__redis.set(key, value, ex=ttl)

  async def delete(self, key: str):
    await self.__redis.delete(key)

  async def close(self):
    self.__redis.close()

  async def pop(self, key: str):
    value = await self.__redis.get(key)
    await self.__redis.delete(key)
    return value