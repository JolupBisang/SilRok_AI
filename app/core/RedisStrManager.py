from core.RedisManager import RedisManager
from core.config import settings

class RedisStrManager(RedisManager):
  def __init__(
    self,
    host: str = settings.REDIS_STR_HOST,
    port: int = settings.REDIS_STR_PORT,
    db: int = settings.REDIS_STR_DB,
    ttl: int = settings.REDIS_STR_TTL,
    decode_responses: bool = settings.REDIS_STR_DECODE_RESPONSES,
    max_memory: str = settings.REDIS_STR_MAX_MEMORY,
    max_memory_policy: str = settings.REDIS_STR_MAX_MEMORY_POLICY,
  ):
    super().__init__(
      host=host,
      port=port,
      db=db,
      ttl=ttl,
      decode_responses=decode_responses,
      max_memory=max_memory,
      max_memory_policy=max_memory_policy
    )