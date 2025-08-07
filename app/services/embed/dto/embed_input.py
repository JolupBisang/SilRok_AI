import numpy as np

from dataclasses import dataclass, field


@dataclass(slots=True)
class EmbedInput:
    user_id: str = field()
    audio: np.ndarray = field(repr=False)
    sample_rate: int = field()
