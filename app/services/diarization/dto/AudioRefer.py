from dataclasses import dataclass, field
import json
import numpy as np


@dataclass(slots=True)
class AudioRefer:  # NOTE 필요 없는데 일단 나둠
    refer_dict: dict[str : list[np.ndarray]] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict):
        return AudioRefer(data)
