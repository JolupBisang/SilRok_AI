from dataclasses import dataclass

from services.rt_diarization.diarization.dto import Speak

from .diarizing_asr_context import DiarizingASRContext


@dataclass(slots=True)
class MergerInput:
    uuid: str
    group_id: str
    user_id: str
    completed: list[Speak]
    candidate: list[Speak]

    @staticmethod
    def from_diarizing_asr_context(context: DiarizingASRContext):
        return MergerInput(
            uuid=context.uuid,
            group_id=context.group_id,
            user_id=context.user_id,
            completed=context.diarization_context.completed,
            candidate=context.diarization_context.candidate,
        )
