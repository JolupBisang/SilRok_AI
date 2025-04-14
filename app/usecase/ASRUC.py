import numpy as np

from ServerObject import ServerObject
from core import settings
from data.dto.request import SttByte, SttFile, SttDuration
from data.dto.response import SentenceResponse
from data.entity import ASREntity, RedisEntity
from services import ASRService, RedisService


class ASRUC(ServerObject):

  @ASRService.object
  @RedisService.object
  def __init__(
    self,
    asr_service:ASRService,
    redis_service:RedisService,
    sample_rate:int = settings.MODEL_SAMPLE_RATE,
  ):
    super().__init__()

    self.asr_service = asr_service
    self.redis_service = redis_service

    self.__SAMPLE_RATE = sample_rate

  async def __transcribe_by_duration(
    self, 
    audio:np.ndarray, 
    group:str,
    user:str,
    language:str = None
  ):

    redis_result = await self.redis_service.load_from_duration(
      group, user
    )
    asr_result = await self.asr_service.transcribe_by_duration(
      ASREntity.from_redis_result(
        redis_result, audio, language
      )
    )
    await self.redis_service.save_to_duration(
      RedisEntity.from_param(asr_result), group, user  
    )

    return SentenceResponse.get_from_asr_result(asr_result)

  async def __transcribe_by_sentence(
    self, 
    audio:np.ndarray, 
    group:str,
    user:str,
    prompt:str = None,
    language:str = None
  ):
    param, p_audio, prev_audio = await self.redis_service.load_from_sentence(
      group, user
    )
    param, completed, candidate = await self.asr_service.transcribe_by_sentence(
      audio, param, p_audio, prev_audio, prompt, language
    )

    await self.redis_service.save_to_sentence(
      param,
      audio = param.audio,
      prev_audio = param.prev_processed_audio,
      group = group,
      user = user
    )

    return completed, candidate

  async def transcribe_from_bytes(self, param:SttByte|SttFile):
    asr = ASREntity(
      audio = await param.get_audio(self.__SAMPLE_RATE),
      prompt = param.prompt,
      language = param.language,
    )
    asr_result = await self.asr_service.transcribe(asr)
    return SentenceResponse.get_from_asr_result(asr_result)

  async def transcribe_by_duration_from_bytes(self, param:SttDuration):
    return await self.__transcribe_by_duration(
      await param.get_audio(self.__SAMPLE_RATE), 
      param.group, param.user, param.language
    )

  # async def transcribe_by_duration_from_opus(
  #   self, audio:bytes, group:str, user:str, language:str
  # ):
  #   audio, _ = decompress_from_opus(audio)
  #   audio = bytes_to_np(io.BytesIO(audio), self.__SAMPLE_RATE)
  #   audio = np.mean(audio, axis=1) if audio.ndim > 1 else audio

  #   completed, candidate = await self.__transcribe_by_duration(
  #     audio, group=group, user=user, language=language
  #   )
  #   result = SentenceResponse.get_from_result(
  #     completed = completed,
  #     candidate = candidate
  #   )

  #   return result