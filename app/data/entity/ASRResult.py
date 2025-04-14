import numpy as np
from dataclasses import dataclass, field

from RTWhisper.data import Param, Sentence, Token
from data.entity import ASREntity


@dataclass
class ASRResult:
  param:Param = field(default_factory=Param)
  completed:dict[int:Sentence] = field(default_factory=dict)
  candidate:list[Token] = field(default_factory=list)
  audio_head:np.ndarray = np.zeros((0,), dtype=np.float32)
  prev_audio:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))

  def extract_asr_entity(self):
    return ASREntity(
      param = self.param,
      audio_head = self.audio_head,
      prev_audio = self.prev_audio,
    )