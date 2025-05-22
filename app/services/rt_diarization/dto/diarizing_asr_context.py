from dataclasses import dataclass, field

import numpy as np

from RTWhisper.data import Param, Sentence

from .diarizing_asr_input import DiarizingASRInput
from .fixed_buffer_clustering import FixedBufferClustering
from .speak import Speak

@dataclass(slots=True)
class DiarizingASRContext:
    uuid: str
    group_id: str
    user_id: str

    # asr param
    param: Param = field(default_factory=Param)
    asr_completed: list[Sentence] = field(default_factory=list)
    asr_candidate: list[Sentence] = field(default_factory=list)

    # diarization param
    clustering: FixedBufferClustering = field(
        default_factory=lambda: FixedBufferClustering({})
    )
    audio: np.ndarray = field(default_factory=lambda: np.zeros((0,), dtype=np.float32))
    offset: int = 0

    diarization_completed: list[Speak] = field(default_factory=list)
    diarization_candidate: list[Speak] = field(default_factory=list)

    def __asr_update(self, audio: np.ndarray, prompt: str = None, language: str = None):
        self.param.audio = np.concatenate([self.param.audio, audio])
        self.param.prompt = prompt
        self.param.language = language
        self.asr_completed = []
        self.asr_candidate = []

    def __diarization_update(self, audio: np.ndarray, refer:dict = {}):
        self.audio = np.concatenate([self.audio, audio])
        self.diarization_completed = []
        self.diarization_candidate = []

        if refer:
            self.clustering = FixedBufferClustering(refer)

    def update(self, X: DiarizingASRInput):
        self.uuid = X.uuid
        if self.group_id != X.group_id:
            raise ValueError("group_id mismatch")
        if self.user_id != X.user_id:
            raise ValueError("user_id mismatch")

        self.__asr_update(X.audio, X.prompt, X.language)
        self.__diarization_update(X.audio, X.refer_dict)

    @staticmethod
    def from_diarizing_asr_input(X: DiarizingASRInput):
        return DiarizingASRContext(
            uuid = X.uuid,
            group_id=X.group_id,
            user_id=X.user_id,
            clustering=FixedBufferClustering(X.refer_dict),
        )
