from dataclasses import dataclass, field
from typing import Union
import numpy as np

from RTWhisper.data import Sentence
from core import settings
from util import FixedBufferClustering

from .Speak import Speak
from .AudioRefer import AudioRefer


@dataclass(slots=True)
class DiarizationContext:
    user_id: str
    clustering: FixedBufferClustering = field(
        default_factory=lambda: FixedBufferClustering({})
    )
    audio: np.ndarray = field(default_factory=lambda: np.zeros((0,), dtype=np.float32))
    offset: int = 0

    completed: Union[list[Sentence], list[Speak]] = field(default_factory=list)
    candidate: Union[list[Sentence], list[Speak]] = field(default_factory=list)

    def update(
        self, audio: np.ndarray, completed: list[Sentence], candidate: list[Sentence]
    ):
        self.audio = np.concatenate([self.audio, audio], axis=0)
        self.completed = completed
        self.candidate = candidate

    @staticmethod
    def get_instance(
        user_id: str,
        ar: AudioRefer = AudioRefer(),
        MAX_SIZE: int = settings.DIARIZATION_MAX_REFER,
    ):
        return DiarizationContext(
            user_id=user_id,
            clustering=FixedBufferClustering(ar.refer_dict, MAX_SIZE),
        )

    def get_users(self, user_id: str = None):
        if user_id is None:
            user_id = self.user_id
        return (
            [s for s in self.completed if s.user_id == user_id],
            [s for s in self.candidate if s.user_id == user_id],
        )
