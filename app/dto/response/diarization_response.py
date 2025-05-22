from pydantic import BaseModel

from services.rt_diarization import RTDiarizationOutput

from .sentence import Sentence

class DiarizationResponse(BaseModel):
    completed: list[Sentence]
    candidate: list[Sentence]

    @staticmethod
    def from_rt_diarization_output(Y: RTDiarizationOutput):
        return DiarizationResponse(
            completed=[Sentence.get_from_speak(speak) for speak in Y.completed],
            candidate=[Sentence.get_from_speak(speak) for speak in Y.candidate],
        )
