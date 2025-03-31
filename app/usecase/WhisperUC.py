import base64
import io
import numpy as np
import json

from ServerObject import ServerObject
from core import RedisByteManager, RedisStrManager, settings
from schemas.whisper import Sentence, SttByte, SttFile, SttStepByte, Word
from services.WhisperService import Sentence as WhisperSentence, Word as WhisperWord
from services.ThreadManagerService import ThreadManagerService
from services.WhisperService import WhisperService
from util.util import audio_to_np

class WhisperUC(ServerObject):

  @ThreadManagerService.object
  @WhisperService.object
  @RedisByteManager.object
  @RedisStrManager.object
  def __init__(
    self,
    thread_manager_service:ThreadManagerService, 
    whisper_service:WhisperService,
    redis_byte_manager:RedisByteManager,
    redis_str_manager:RedisStrManager,
    sample_rate:int = settings.MODEL_SAMPLE_RATE,
  ) -> None:
    super().__init__()

    self.__SAMPLE_RATE = sample_rate

    self.thread_manager_service = thread_manager_service
    self.whisper_service = whisper_service
    self.redis_byte_manager = redis_byte_manager
    self.redis_str_manager = redis_str_manager
    
  async def get_pre_data(self, group:str, user:str):
    pre_data = await self.redis_str_manager.pop(f"whisper:{group}:{user}:data")
    if pre_data is not None:
      data = json.loads(pre_data)
      order = data["order"]
      pre_sentence = None
      if data["pre_sentence"]:
        pre_sentence = WhisperSentence(
          lang = data["pre_sentence"]["lang"],
          text = data["pre_sentence"]["text"],
          audio = None,
          tokens = [
            WhisperWord(
              start = word["start"],
              end = word["end"],
              text = word["text"]
            ) for word in data["pre_sentence"]["words"]
          ]
        )
      pre_recog = []
      for idx, pr in enumerate(data["pre_recog"]):
        pre_recog.append(WhisperSentence(
          lang = pr["lang"],
          text = pr["text"],
          audio = np.frombuffer(await self.redis_byte_manager.pop(f"whisper:{group}:{user}:audio:{idx}"), dtype=np.float32),
          tokens = [
            WhisperWord(
              start = word["start"],
              end = word["end"],
              text = word["text"]
            ) for word in pr["words"]
          ]
        ))
      return order, pre_sentence, pre_recog
    return 0, None, []
      
  async def set_pre_data(
    self, 
    group:str, 
    user:str, 
    order:int,
    pre_sentence:WhisperSentence,
    pre_recog:list[WhisperSentence]
  ):
    data = {
      "order": order,
      "pre_sentence": {},
      "pre_recog": []
    }

    if pre_sentence:
      data["pre_sentence"] = {
        "lang": pre_sentence.lang,
        "text": pre_sentence.text,
        "words": [
          {
            "start": word.start,
            "end": word.end,
            "text": word.text
          } for word in pre_sentence.words
        ]
      }
      
    if pre_recog:
      for idx, sentence in enumerate(pre_recog):
        data["pre_recog"].append({
          "lang": sentence.lang,
          "text": sentence.text,
          "words": [
            {
              "start": word.start,
              "end": word.end,
              "text": word.text
            } for word in sentence.words
          ]
        })
        await self.redis_byte_manager.set(f"whisper:{group}:{user}:audio:{idx}", sentence.audio.tobytes())

    await self.redis_str_manager.set(
      f"whisper:{group}:{user}:data",
      json.dumps(data),
    )
    
  async def recognition_step(
    self, 
    audio:np.ndarray, 
    group:str,
    user:str,
    prompt:str,
    language:str = None
  ) -> dict:

    order, pre_sentence, pre_recog = await self.get_pre_data(group, user)

    completed_dict, order, pre_sentence, pre_recog = await self.thread_manager_service.submit_to_executor(
      self.whisper_service.recognition_step,
      audio, order, prompt=prompt,
      pre_sentence=pre_sentence, pre_recog=pre_recog,
      language=language
    )

    await self.set_pre_data(group, user, order, pre_sentence, pre_recog)

    new_dict = {}
    for key, value in completed_dict.items():
      new_dict[key] = self.sentence_to_response(value)
    for idx, s in enumerate(pre_recog):
      new_dict[f"c{idx}"] = self.sentence_to_response(s)
    
    return new_dict
  
  async def recognition(
    self, 
    audio:np.ndarray, 
    prompt:str,
    language:str = None
  ) -> dict:

    sentences = await self.thread_manager_service.submit_to_executor(
      self.whisper_service.recognition,
      audio, prompt=prompt, language=language
    )

    new_sentences = []
    for sentence in sentences:
      new_sentences.append(self.sentence_to_response(sentence))

    return new_sentences

  def sentence_to_response(self, sentence:WhisperSentence) -> Sentence:
    return Sentence(
        lang = sentence.lang,
        text = sentence.text,
        words = [
          Word(
            start = word.start,
            end = word.end,
            text = word.text
          ) for word in sentence.words
        ]
      )
      
  async def recognition_files(self, params: SttFile) -> dict:
    audio = await params.audio.read()
    audio = audio_to_np(audio, self.__SAMPLE_RATE)

    return await self.recognition(audio, prompt = params.prompt, language=params.language)

  async def recognition_bytes(self, params: SttByte) -> dict:
    audio = base64.b64decode(params.audio)
    audio = io.BytesIO(audio)
    audio = audio_to_np(audio, self.__SAMPLE_RATE)

    return await self.recognition(audio, prompt = params.prompt, language=params.language)

  async def recognition_step_bytes(self, params: SttStepByte) -> dict:
    audio = base64.b64decode(params.audio)
    audio = io.BytesIO(audio)
    audio = audio_to_np(audio, self.__SAMPLE_RATE)

    return await self.recognition_step(
      audio, 
      group=params.group, user=params.user,
      prompt = params.prompt, 
      language=params.language
    )