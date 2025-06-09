from dataclasses import dataclass, field

import numpy as np

from rt_whisper.data import Param, Sentence

from .diarizing_asr_input import DiarizingASRInput
from .fixed_buffer_clustering import FixedBufferClustering
from .speak import Speak


@dataclass(slots=True)
class DiarizingASRContext:
    uuid: str = field()
    group_id: str = field()
    user_id: str = field()

    # asr param
    param: Param = field(default_factory=Param, repr=False)
    asr_completed: list[Sentence] = field(default_factory=list, repr=False)
    asr_candidate: list[Sentence] = field(default_factory=list, repr=False)

    # diarization param
    clustering: FixedBufferClustering = field(
        default_factory=lambda: FixedBufferClustering({}), repr=False
    )
    audio: np.ndarray = field(
        default_factory=lambda: np.zeros((0,), dtype=np.float32), repr=False
    )
    offset: int = field(default=0, repr=False)

    diarization_completed: list[Speak] = field(default_factory=list, repr=False)
    diarization_candidate: list[Speak] = field(default_factory=list, repr=False)

    def __asr_update(self, audio: np.ndarray, prompt: str = None, language: str = None):
        self.param.chunk = np.concatenate([self.param.chunk, audio])
        self.param.prompt = prompt
        self.param.language = language
        self.asr_completed = []
        self.asr_candidate = []

    def __diarization_update(self, audio: np.ndarray, refer: dict = {}):
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

        if X.sc_offset is not None:
            self.__init__(
                uuid=self.uuid,
                user_id=self.user_id,
                group_id=self.group_id,
                clustering=self.clustering,
            )
            self.param.offset = X.sc_offset
            self.offset = X.sc_offset
        self.__asr_update(X.audio, X.prompt, X.language)
        self.__diarization_update(X.audio, X.refer_dict)

    @staticmethod
    def from_diarizing_asr_input(X: DiarizingASRInput):
        context = DiarizingASRContext(
            uuid=X.uuid,
            group_id=X.group_id,
            user_id=X.user_id,
            clustering=FixedBufferClustering(X.refer_dict),
        )

        if X.sc_offset is not None:
            context.param.offset = X.sc_offset
            context.offset = X.sc_offset

        return context
