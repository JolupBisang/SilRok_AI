from dataclasses import dataclass, field
import numpy as np
import json

from RTWhisper.data import Param
from data.entity import ASRResult

@dataclass
class RedisEntity:
  param:Param = field(default_factory=Param)
  audio_head:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  prev_audio:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))

  def param_dump(self):
    return json.dumps(self.param.to_dict())

  def audio_head_bytes(self):
    return self.audio_head.tobytes()
  
  def prev_audio_bytes(self):
    return self.prev_audio.tobytes()

  @staticmethod
  def from_param(asr_result:ASRResult):
    return RedisEntity(
      param = asr_result.param,
      audio_head = asr_result.audio_head,
      prev_audio = asr_result.prev_audio,
    )

