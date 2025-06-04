from dataclasses import dataclass, field

from .diarizing_asr_context import DiarizingASRContext
from .speak import Speak


@dataclass(slots=True)
class DiarizingASROutput:
    uuid: str = field()
    group_id: str = field()
    user_id: str = field()
    completed: list[Speak] = field()
    candidate: list[Speak] = field()

    @staticmethod
    def from_diarizing_asr_context(context: DiarizingASRContext):
        return DiarizingASROutput(
            uuid=context.uuid,
            group_id=context.group_id,
            user_id=context.user_id,
            completed=context.diarization_completed,
            candidate=context.diarization_candidate,
        )
