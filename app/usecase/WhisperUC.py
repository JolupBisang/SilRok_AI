import base64
import io
import numpy as np
import json

from ServerObject import ServerObject
from core import RedisByteManager, RedisStrManager, settings
from schemas.whisper import DurationResponse, Sentence, SentenceResponse, SttByte, SttFile, SttDuration, Word
from services import ThreadManagerService
from services.whisper import SentenceParams, WordParams, WordService, SentenceService, Service
from services.whisper import Sentence as WhisperSentence
from services.whisper import Word as WhisperWord
from util.util import audio_to_np

class WhisperUC(ServerObject):

  @ThreadManagerService.object
  @WordService.object
  @SentenceService.object
  @Service.object
  @RedisByteManager.object
  @RedisStrManager.object
  def __init__(
    self,
    thread_manager_service:ThreadManagerService, 
    word_service:WordService,
    sentence_service:SentenceService,
    service:Service,
    redis_byte_manager:RedisByteManager,
    redis_str_manager:RedisStrManager,
    sample_rate:int = settings.MODEL_SAMPLE_RATE,
    min_audio_duration:int = settings.MIN_AUDIO_DURATION,
  ) -> None:
    super().__init__()

    self.__SAMPLE_RATE = sample_rate
    self.__MIN_AUDIO_DURATION = min_audio_duration

    self.thread_manager_service = thread_manager_service
    self.word_service = word_service
    self.sentence_service = sentence_service
    self.service = service
    self.redis_byte_manager = redis_byte_manager
    self.redis_str_manager = redis_str_manager
    
  # 오디오 데이터는 추후 병렬처리와 효율성을 위해 shared memory로 변경 필요
  async def __load_data(
    self,
    data_key:str,
    audio_key:str,
    prev_audio_key:str,
  ):
    param = await self.redis_str_manager.pop(data_key)
    param = json.loads(param) if param else None
    audio = await self.redis_byte_manager.pop(audio_key)
    audio = None if audio is None else np.frombuffer(audio, dtype=np.float32)
    prev_audio = await self.redis_byte_manager.pop(prev_audio_key)
    prev_audio = None if prev_audio is None else np.frombuffer(prev_audio, dtype=np.float32) 
    return param, audio, prev_audio
    
  async def __save_data(
    self,
    param,
    audio:np.ndarray,
    prev_audio:np.ndarray,
    data_key:str,
    audio_key:str,
    prev_audio_key:str,
  ):
    await self.redis_str_manager.set(data_key, json.dumps(param.to_dict()))
    if audio is not None:
      await self.redis_byte_manager.set(audio_key, audio.tobytes())
    if prev_audio is not None:
      await self.redis_byte_manager.set(prev_audio_key, prev_audio.tobytes())
    
  async def __transcribe_by_duration(
    self, 
    audio:np.ndarray, 
    group:str,
    user:str,
    language:str = None
  ) -> dict:
    param, p_audio, prev_audio = await self.__load_data(
      f"whisper:{group}:{user}:tdd",
      f"whisper:{group}:{user}:tda",
      f"whisper:{group}:{user}:tdpa"
    )
    param = WordParams.from_dict(param) if param else WordParams()
    if p_audio is not None:
      audio = np.concatenate([p_audio, audio])
    param.audio = audio
    param.prev_audio = prev_audio
    param.language = language

    if audio.shape[0] < self.__MIN_AUDIO_DURATION:
      p_audio = audio

      await self.__save_data(
        param,
        audio = p_audio,
        prev_audio = prev_audio,
        data_key = f"whisper:{group}:{user}:tdd",
        audio_key = f"whisper:{group}:{user}:tda",
        prev_audio_key = f"whisper:{group}:{user}:tdpa"
      )

      result = DurationResponse(
        completed = [],
        candidate = [],
      )

      return result
      
    result, _ = await self.thread_manager_service.submit_to_executor(
      self.word_service.transcribe, param
    )

    param.order = result.order
    param.time_offset = result.time_offset
    param.prev_audio = result.prev_audio
    param.prev_words = result.prev_words
    param.prev_recog = result.prev_recog
    param.prev_prob_mean = result.prev_prob_mean
    param.prev_prob_std = result.prev_prob_std
    param.prev_prob_count = result.prev_prob_count
    param.prev_dura_mean = result.prev_dura_mean
    param.prev_dura_std = result.prev_dura_std
    param.prev_dura_count = result.prev_dura_count

    await self.__save_data(
      param,
      audio = None,
      prev_audio = result.prev_audio,
      data_key = f"whisper:{group}:{user}:tdd",
      audio_key = f"whisper:{group}:{user}:tda",
      prev_audio_key = f"whisper:{group}:{user}:tdpa"
    )

    result = DurationResponse(
      completed = [self.__sentence_to_response(key, value) 
        for key, value in result.completed_dict.items()],     
      candidate = [self.__word_to_response(word) 
       for word in [*result.prev_words, *result.prev_recog]],
    )

    return result

  async def __transcribe_by_sentence(
    self, 
    audio:np.ndarray, 
    group:str,
    user:str,
    prompt:str = None,
    language:str = None
  ) -> dict:
    param, p_audio, prev_audio = await self.__load_data(
      f"whisper:{group}:{user}:tsp",
      f"whisper:{group}:{user}:tsa",
      f"whisper:{group}:{user}:tspa"
    )
    if p_audio is not None:
      audio = np.concatenate([p_audio, audio])
    param = SentenceParams.from_dict(param) if param else SentenceParams()

    param.audio = audio
    param.prev_audio = prev_audio
    param.language = language
    param.prompt = prompt

    if audio.shape[0] < self.__MIN_AUDIO_DURATION:
      p_audio = audio

      await self.__save_data(
        param,
        audio = p_audio,
        prev_audio = prev_audio,
        data_key = f"whisper:{group}:{user}:tsp",
        audio_key = f"whisper:{group}:{user}:tsa",
        prev_audio_key = f"whisper:{group}:{user}:tspa"
      )

      result = SentenceResponse(
        completed = [],
        candidate = [],
      )

      return result

    result, audio = await self.thread_manager_service.submit_to_executor(
      self.sentence_service.transcribe, param
    )

    param.order = result.order
    param.time_offset = result.time_offset
    param.prev_audio = result.prev_audio
    param.prev_sentence = result.prev_sentence

    await self.__save_data(
      param,
      audio = None,
      prev_audio = result.prev_audio,
      data_key = f"whisper:{group}:{user}:tsp",
      audio_key = f"whisper:{group}:{user}:tsa",
      prev_audio_key = f"whisper:{group}:{user}:tspa"
    )

    result = SentenceResponse(
      completed = [self.__sentence_to_response(key, value)
       for key, value in result.completed_dict.items()],
      candidate = [self.__word_to_response(key) for key in result.prev_recog],
    )

    return result

  async def __transcribe(
    self,
    audio:np.ndarray,
    prompt:str = None,
    lanuage:str = None,
  ):
    
    result = await self.thread_manager_service.submit_to_executor(
      self.service.transcribe, audio, lanuage, prompt
    )

    new_result = []
    for i, sentence in enumerate(result):
      new_result.append(self.__sentence_to_response(i, sentence))

    return new_result

  def __sentence_to_response(self, order:int, sentence:WhisperSentence) -> Sentence:
    return Sentence(
      order = order,
      lang = sentence.lang,
      text = sentence.text,
      words = [
        self.__word_to_response(word) for word in sentence.words
      ]
    )

  def __word_to_response(self, word:WhisperWord) -> Word:
    return Word(
      start = word.start,
      end = word.end,
      text = word.text,
      lang = word.lang
    )
      
  async def transcribe_from_file(self, params: SttFile) -> dict:
    audio = await params.audio.read()
    audio = audio_to_np(audio, self.__SAMPLE_RATE)

    return await self.__transcribe(audio, prompt = params.prompt, language=params.language)

  async def transcribe_from_byte(self, params: SttByte) -> dict:
    audio = base64.b64decode(params.audio)
    audio = io.BytesIO(audio)
    audio = audio_to_np(audio, self.__SAMPLE_RATE)

    return await self.__transcribe(audio, prompt = params.prompt, language=params.language)

  async def transcribe_by_duration_from_byte(self, params: SttDuration) -> dict:
    audio = base64.b64decode(params.audio)
    audio = io.BytesIO(audio)
    audio = audio_to_np(audio, self.__SAMPLE_RATE)

    return await self.__transcribe_by_duration(
      audio, 
      group=params.group, user=params.user,
      language=params.language
    )