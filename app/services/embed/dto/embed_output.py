from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class EmbedOutput:
    embedding: np.ndarray
