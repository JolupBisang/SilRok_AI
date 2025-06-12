from dataclasses import dataclass, field

from .merger_input import MergerInput
from .speak import Speak

MIN_WAITED_TIME = 16000 * 5


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
        recent_time = max(self.sync_timestamp.values())

        # 오랫동안 인식된 말이 없는 사용자 제거
        if recent_time - base_time > MIN_WAITED_TIME:
            anchor = recent_time - MIN_WAITED_TIME
            keys = list(self.sync_timestamp.keys())
            for user_id in keys:
                if self.sync_timestamp[user_id] < anchor:
                    del self.sync_timestamp[user_id]
                    self.cached_completed[user_id] += self.cached_candidate[user_id]
                    # del 해도 되는데, self.cached_completed의 키와 일관성 가지기 위해
                    self.cached_candidate[user_id] = []
            base_time = min(self.sync_timestamp.values())

        new_completed = []
        new_candidate = []

        for user_id in self.cached_completed.keys():
            co, ca = [], []
            for speak in self.cached_completed[user_id]:
                if speak.sentence.tokens[-1].end <= base_time:
                    co.append(speak)
                else:
                    ca.append(speak)
            new_completed += co
            new_candidate += ca
            self.cached_completed[user_id] = ca

        new_candidate += [
            s for speaks in self.cached_candidate.values() for s in speaks
        ]

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
