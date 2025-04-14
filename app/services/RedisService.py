import json
import numpy as np

from RTWhisper.data import Param
from ServerObject import ServerObject
from core import RedisByteManager, RedisStrManager
from data.entity import RedisEntity, RedisResult

class RedisService(ServerObject):
  
  @RedisByteManager.object
  @RedisStrManager.object
  def __init__(
    self,
    redis_byte_manager:RedisByteManager,
    redis_str_manager:RedisStrManager,
  ) -> None:
    super().__init__()
    
    self.redis_byte_manager = redis_byte_manager
    self.redis_str_manager = redis_str_manager

  async def __save_data(
    self,
    redis_entity:RedisEntity,
    data_key:str,
    audio_head_key:str,
    prev_audio_key:str,
  ):
    await self.redis_str_manager.set(data_key, redis_entity.param_dump())
    if len(redis_entity.audio_head) > 0:
      await self.redis_byte_manager.set(
        audio_head_key, redis_entity.audio_head_bytes()
      )
    if len(redis_entity.prev_audio) > 0:
      await self.redis_byte_manager.set(
        prev_audio_key, redis_entity.prev_audio_bytes()
      )

  # 오디오 데이터는 추후 병렬처리와 효율성을 위해 shared memory로 변경 필요
  async def __load_data(
    self,
    data_key:str,
    audio_key:str,
    prev_audio_key:str,
  ):
    param = await self.redis_str_manager.pop(data_key)
    param = Param.from_dict(json.loads(param)) if param else Param()

    audio_head = await self.redis_byte_manager.pop(audio_key)
    audio_head = np.zeros((0,), dtype=np.float32) if audio_head is None else np.frombuffer(audio_head, dtype=np.float32)

    prev_audio = await self.redis_byte_manager.pop(prev_audio_key)
    prev_audio = np.zeros((0,), dtype=np.float32) if prev_audio is None else np.frombuffer(prev_audio, dtype=np.float32) 

    return RedisResult(
      param = param,
      audio_head = audio_head,
      prev_audio = prev_audio
    )

  async def load_from_duration(self, group:str, user:str):
    return await self.__load_data(
      f"whisper:{group}:{user}:tdd",
      f"whisper:{group}:{user}:tdah",
      f"whisper:{group}:{user}:tdpa"
    )

  async def save_to_duration(
    self,
    redis_entity:RedisEntity,
    group:str,
    user:str
  ):
    await self.__save_data(
      redis_entity,
      f"whisper:{group}:{user}:tdd",
      f"whisper:{group}:{user}:tdah",
      f"whisper:{group}:{user}:tdpa"
    )

  async def load_from_sentence(self, group:str, user:str):
    return await self.__load_data(
      f"whisper:{group}:{user}:tsd",
      f"whisper:{group}:{user}:tsah",
      f"whisper:{group}:{user}:tspa"
    )

  async def save_to_sentence(
    self,
    redis_entity:RedisEntity,
    group:str,
    user:str
  ):
    await self.__save_data(
      redis_entity,
      f"whisper:{group}:{user}:tsd",
      f"whisper:{group}:{user}:tsah",
      f"whisper:{group}:{user}:tspa"
    )