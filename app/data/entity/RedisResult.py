from dataclasses import dataclass, field
import numpy as np

from RTWhisper.data import Param

@dataclass
class RedisResult:
  param:Param = field(default_factory=Param)
  audio_head:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))
  prev_audio:np.ndarray = field(
    default_factory=lambda: np.zeros((0,), dtype=np.float32))