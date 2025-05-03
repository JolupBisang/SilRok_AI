from pydantic import BaseModel

from services.asr.dto import ASRContext
from services.diarization.dto import DiarizationContext

from .Sentence import Sentence


class SentenceResponse(BaseModel):
    completed: list[Sentence]
    candidate: list[Sentence]

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
