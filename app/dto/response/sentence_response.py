from pydantic import BaseModel

from services.asr import ASRContext
from services.diarization import DiarizationContext
from services.rt_diarization import RTDiarizationOutput

from .sentence import Sentence


class SentenceResponse(BaseModel):
    completed: list[Sentence]
    candidate: list[Sentence]

    # TODO 여기에 생성하는 것은 옳지 않음
    @staticmethod
    def from_asr_context(ac: ASRContext):
        return SentenceResponse(
            completed=[
                Sentence.get_from_sentence(sentence) for sentence in ac.completed
            ],
            candidate=[
                Sentence.get_from_sentence(sentence) for sentence in ac.candidate
            ],
        )

    @staticmethod
    def from_diarization_context(dc: DiarizationContext):
        completed, candidate = dc.get_users()
        return SentenceResponse(
            completed=[Sentence.get_from_speak(speak) for speak in completed],
            candidate=[Sentence.get_from_speak(speak) for speak in candidate],
        )

    @staticmethod
    def from_rt_diarization_output(Y: RTDiarizationOutput):
        return SentenceResponse(
            completed=[Sentence.get_from_speak(speak) for speak in Y.completed],
            candidate=[Sentence.get_from_speak(speak) for speak in Y.candidate],
        )
