from dataclasses import dataclass, field

from .merger_input import MergerInput
from .speak import Speak


@dataclass(slots=True)
class MergerContext:
    uuid: str = field()
    group_id: str = field()
    completed: list[Speak] = field(default_factory=list, repr=False)
    candidate: list[Speak] = field(default_factory=list, repr=False)

    prev_completed: list[Speak] = field(default_factory=list, repr=False)
    prev_candidate: list[Speak] = field(default_factory=list, repr=False)

    cached_completed: dict[str, list[Speak]] = field(default_factory=dict, repr=False)
    cached_candidate: dict[str, list[Speak]] = field(default_factory=dict, repr=False)
    sync_timestamp: dict[str, int] = field(default_factory=dict, repr=False)
    speak_order: int = field(default=0, repr=False)

    def update(self, X: MergerInput):
        if self.group_id != X.group_id:
            raise ValueError("group_id mismatch")
        self.uuid = X.uuid

        self.prev_completed = self.completed
        self.prev_candidate = self.candidate

        if not X.completed and not X.candidate:
            self.completed = []
            self.candidate = []
            return

        # Update last completed timestamp for each user
        if X.user_id not in self.sync_timestamp:
            self.sync_timestamp[X.user_id] = 0
        if X.completed:
            self.sync_timestamp[X.user_id] = X.completed[-1].sentence.tokens[-1].end

        # Update completed and candidate lists
        self.cached_completed[X.user_id] = X.completed
        self.cached_candidate[X.user_id] = X.candidate

        base_time = min(self.sync_timestamp.values())

        all_completed = [s for speaks in self.cached_completed.values() for s in speaks]
        all_candidate = [s for speaks in self.cached_candidate.values() for s in speaks]

        new_completed = [
            c for c in all_completed if c.sentence.tokens[-1].end <= base_time
        ]
        new_candidate = [c for c in all_completed if c not in new_completed]
        new_candidate += all_candidate

        new_completed.sort(key=lambda x: x.sentence.tokens[0].start)
        new_candidate.sort(key=lambda x: x.sentence.tokens[0].start)

        self.completed = new_completed
        self.candidate = new_candidate

    def set_result(self, completed: list[Speak], candidate: list[Speak]):

        for speak in completed:
            speak.sentence.order = self.speak_order
            self.speak_order += 1

        speak_order = self.speak_order
        for speak in candidate:
            speak.sentence.order = speak_order
            speak_order += 1

        self.completed = completed
        self.candidate = candidate

    @staticmethod
    def from_merger_input(X: MergerInput):
        return MergerContext(
            uuid=X.uuid,
            group_id=X.group_id,
        )
