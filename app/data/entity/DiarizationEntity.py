from dataclasses import dataclass, field
import numpy as np

from RTWhisper.data import Sentence
from util import FixedBufferClustering


@dataclass
class DiarizationEntity:
  clustering:FixedBufferClustering = field(
    default_factory = lambda : FixedBufferClustering({}))
  audio:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  userId:int = None
  completed:dict[int:Sentence] = field(default_factory=dict)
  candidate:list[Sentence] = field(default_factory=list)
  rcd_audio:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  offset:int = 0

  @staticmethod
  def init(refer_dict:dict):
    return DiarizationEntity(
      clustering=FixedBufferClustering(refer_dict),
      rcd_audio=np.zeros((0,), dtype=np.float32),
      offset=0,
    )

  def get_audio(self):
    return np.concatenate([self.rcd_audio, self.audio], axis=0)
  