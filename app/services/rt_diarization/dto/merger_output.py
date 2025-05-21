from dataclasses import dataclass

from services.rt_diarization.diarization import Speak

from .merger_context import MergerContext


@dataclass(slots=True)
class MergerOutput:
    uuid: str
    group_id: str
    completed: list[Speak]
    candidate: list[Speak]

    @staticmethod
    def __is_same_current_with_prev(
        prev_co: list[Speak],
        curr_co: list[Speak],
        prev_ca: list[Speak],
        curr_ca: list[Speak]
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
            context.candidate
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
