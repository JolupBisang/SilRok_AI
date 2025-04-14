import numpy as np
from RTWhisper import SentenceStreamer, TokenStreamer, Transcriber
from RTWhisper.data import Result
from ServerObject import ServerObject
from core import settings
from data.entity import ASREntity, ASRResult

from .ThreadManagerService import ThreadManagerService

class ASRService(ServerObject):
  
  @ThreadManagerService.object
  @Transcriber.object
  @TokenStreamer.object
  @SentenceStreamer.object
  def __init__(
    self,
    thread_manager_service:ThreadManagerService, 
    transcriber:Transcriber,
    token_streamer:TokenStreamer,
    sentence_streamer:SentenceStreamer,
    MIN_AUDIO_DURATION:int = settings.MIN_AUDIO_DURATION
  ) -> None:
    super().__init__()

    self.thread_manager_service = thread_manager_service
    self.transcriber = transcriber
    self.token_streamer = token_streamer
    self.sentence_streamer = sentence_streamer

    self.__MIN_AUDIO_DURATION = MIN_AUDIO_DURATION

  async def __transcribe_wrapper(self, asr_entity:ASREntity, func:callable):
    param = asr_entity.get_composed_param()
    if len(param.audio) < self.__MIN_AUDIO_DURATION:
      return ASRResult(
        param = param, 
        audio_head = param.audio, 
        prev_audio = param.prev_processed_audio
      )

    result:Result = await self.thread_manager_service.submit_to_executor(
      func , param
    )

    param.update(result)

    return ASRResult(
      param = param,
      completed = result.completed,
      candidate = [*result.prev_words, *result.prev_recog],
      prev_audio = param.prev_processed_audio,
    )

  async def transcribe_by_duration(self, asr_entity:ASREntity):
    return await self.__transcribe_wrapper(asr_entity, self.token_streamer.process)

  async def transcribe_by_sentence(self, asr_entity:ASREntity):
    return await self.__transcribe_wrapper(asr_entity, self.sentence_streamer.process)

  async def transcribe(self, asr_entity:ASREntity):
    return await self.__transcribe_wrapper(asr_entity, self.transcriber.process)