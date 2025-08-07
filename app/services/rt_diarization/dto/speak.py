from dataclasses import dataclass, field
from rapidfuzz.distance import Levenshtein

from rt_whisper.data import Sentence


@dataclass(slots=True)
class Speak:
    similarity: float = field()
    user_id: str = field()
    audio_id: str = field()
    sentence: Sentence = field()

    def to_dict(self):
        return {
            "similarity": self.similarity,
            "user_id": self.user_id,
            "audio_id": self.audio_id,
            "sentence": self.sentence.model_dump(),
        }

    def similar(self, other: "Speak"):
        a_start = self.sentence.tokens[0].start
        a_end = self.sentence.tokens[-1].end
        b_start = other.sentence.tokens[0].start
        b_end = other.sentence.tokens[-1].end

        iou = max(0, min(a_end, b_end) - max(a_start, b_start)) / (
            max(a_end, b_end) - min(a_start, b_start)
        )
        ratio = Levenshtein.normalized_similarity(
            self.sentence.text, other.sentence.text
        )

        return (ratio + iou) / 2

    @staticmethod
    def from_dict(data: dict):
        return Speak(
            similarity=data["similarity"],
            user_id=data["user_id"],
            audio_id=data["audio_id"],
            sentence=Sentence(**data["sentence"]),
        )

__all__ = ["Speak"]
