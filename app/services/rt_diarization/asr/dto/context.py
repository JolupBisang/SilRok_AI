from dataclasses import field, dataclass
import numpy as np

from RTWhisper.data import Param, Sentence


@dataclass(slots=True)
class Context:
    param: Param = field(default_factory=Param)
    completed: list[Sentence] = field(default_factory=list)
    candidate: list[Sentence] = field(default_factory=list)

    def update(self, audio: np.ndarray, prompt: str = None, language: str = None):
        self.param.audio = np.concatenate([self.param.audio, audio])
        self.param.prompt = prompt
        self.param.language = language
        self.completed = []
        self.candidate = []
