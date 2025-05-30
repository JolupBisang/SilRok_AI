from pydantic import BaseModel

from services.rt_diarization import RTDiarizationOutput

from .sentence import Sentence

class DiarizationResponse(BaseModel):
    group_id: str
    completed: list[Sentence]
    candidate: list[Sentence]

    @staticmethod
    def from_rt_diarization_output(Y: RTDiarizationOutput):
        return DiarizationResponse(
            group_id=Y.group_id,
            completed=[Sentence.get_from_speak(speak) for speak in Y.completed],
            candidate=[Sentence.get_from_speak(speak) for speak in Y.candidate],
        )
