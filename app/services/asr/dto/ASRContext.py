from dataclasses import field, dataclass
import numpy as np

from RTWhisper.data import Param, Sentence


@dataclass(slots=True)
class ASRContext:
    param: Param = field(default_factory=Param)
    completed: list[Sentence] = field(default_factory=list)
    candidate: list[Sentence] = field(default_factory=list)

    def update(self, audio: np.ndarray, prompt: str = None, language: str = None):
        self.param.audio = np.concatenate([self.param.audio, audio])
        self.param.prompt = prompt
        self.param.language = language
        self.completed = []
        self.candidate = []

    @staticmethod
    def get_instance(audio: np.ndarray, prompt: str, language: str):
        asr_context = ASRContext()
        asr_context.param.audio = audio
        asr_context.param.prompt = prompt
        asr_context.param.language = language
        return asr_context
