from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class DiarizingASRInput:
    uuid: str
    audio: np.ndarray
    group_id: str
    user_id: str
    refer_dict: dict = field(default_factory=dict)
    prompt: str = field(default=None)
    language: str = field(default=None)

    # 임의 변수
    must_return:bool = field(default=False)
