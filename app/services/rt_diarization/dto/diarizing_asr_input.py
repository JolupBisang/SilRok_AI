import numpy as np

from dataclasses import dataclass, field


@dataclass(slots=True)
class DiarizingASRInput:
    uuid: str = field()
    audio: np.ndarray = field(repr=False)
    group_id: str = field()
    user_id: str = field()
    refer_dict: dict = field(default_factory=dict, repr=False)
    prompt: str | None = field(default=None)
    language: str | None = field(default=None)
    sc_offset: int | None = field(default=None)

    # 임의 변수
    must_return: bool = field(default=False, repr=False)


__all__ = ["DiarizingASRInput"]
