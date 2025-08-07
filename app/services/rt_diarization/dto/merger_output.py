from dataclasses import dataclass, field

from services.rt_diarization.dto.merger_context import MergerContext
from services.rt_diarization.dto.speak import Speak


@dataclass(slots=True)
class MergerOutput:
    uuid: str = field()
    group_id: str = field()
    completed: list[Speak] = field()
    candidate: list[Speak] = field()

    @staticmethod
    def __is_same_current_with_prev(
        prev_co: list[Speak],
        curr_co: list[Speak],
        prev_ca: list[Speak],
        curr_ca: list[Speak],
    ) -> int:
        if len(prev_co) != len(curr_co):
            return False
        if len(prev_ca) != len(curr_ca):
            return False

        for p, c in zip(prev_co, curr_co):
            if p.sentence.text != c.sentence.text or p.user_id != c.user_id:
                return False

        for p, c in zip(prev_ca, curr_ca):
            if p.sentence.text != c.sentence.text or p.user_id != c.user_id:
                return False

        return True

    @staticmethod
    def from_merger_context(context: MergerContext):
        if MergerOutput.__is_same_current_with_prev(
            context.prev_completed,
            context.completed,
            context.prev_candidate,
            context.candidate,
        ):
            return MergerOutput(
                uuid=context.uuid,
                group_id=context.group_id,
                completed=[],
                candidate=[],
            )

        return MergerOutput(
            uuid=context.uuid,
            group_id=context.group_id,
            completed=context.completed,
            candidate=context.candidate,
        )

__all__ = ["MergerOutput"]
