from dataclasses import field, dataclass
import numpy as np

from RTWhisper.data import Param
from data.entity import RedisResult

@dataclass
class ASREntity:
  audio: np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  param: Param = field(default_factory=Param)
  audio_head: np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  prev_audio: np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  prompt:str = None
  language:str = None

  __combined_audio:np.ndarray = field(default=None, init=False, repr=False)

  @property
  def combined_audio(self):
    if self.__combined_audio is None:
      self.__combined_audio = np.concatenate([self.audio_head, self.audio])
    return self.__combined_audio

  def get_composed_param(self):
    self.param.audio = self.combined_audio
    self.param.prev_processed_audio = self.prev_audio
    self.param.language = self.language
    self.param.prompt = self.prompt

    return self.param

  @staticmethod
  def from_redis_result(
    redis_result:RedisResult, 
    audio:np.ndarray, 
    language:str = None, 
    prompt:str = None
  ):
    return ASREntity(
      audio = audio,
      param = redis_result.param,
      audio_head = redis_result.audio_head,
      prev_audio = redis_result.prev_audio,
      prompt = prompt,
      language = language
    )

    