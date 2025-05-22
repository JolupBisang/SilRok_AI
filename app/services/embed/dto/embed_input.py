
from dataclasses import dataclass
import numpy as np


@dataclass(slots = True)
class EmbedInput:
    audio:np.ndarray
    sample_rate:int
