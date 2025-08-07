from dataclasses import dataclass, field

from services.llm.dto.flag import DONE, REQUEST, UPDATE


@dataclass(slots=True)
class LLMInput:
    group_id: str = field()
    conversation: str = field(default="")
    mode: str = field(default=REQUEST)
    agenda: list[str] | None = field(default=None)
    num_people: int | None = field(default=None)
    meeting_topic: str | None = field(default=None)

    # Override
    def __post_init__(self):
        if self.mode not in [DONE, REQUEST, UPDATE]:
            raise ValueError(
                f"Invalid mode: {self.mode}. Must be one of {DONE}, {REQUEST}, {UPDATE}."
            )

__all__ = ["LLMInput"]
