from typing import Any, Callable
from pydantic import BaseModel

from services.rt_diarization import RTDiarizationOutput

from .sentence import Sentence


class DiarizationResponse(BaseModel):
    group_id: str
    completed: list[Sentence]
    candidate: list[Sentence]

    # NOTE front 요청으로 임의 설정
    flag: str = "diarized"

    def to_byte(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump())
        return len(bt).to_bytes(4, "big") + bt

    @staticmethod
    def from_rt_diarization_output(Y: RTDiarizationOutput):
        return DiarizationResponse(
            group_id=Y.group_id,
            completed=[Sentence.get_from_speak(speak) for speak in Y.completed],
            candidate=[Sentence.get_from_speak(speak) for speak in Y.candidate],
        )
