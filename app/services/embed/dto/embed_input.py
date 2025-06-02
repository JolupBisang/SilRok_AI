
from dataclasses import dataclass
import numpy as np


@dataclass(slots = True)
class EmbedInput:
    user_id: str
    audio:np.ndarray
    sample_rate:int
