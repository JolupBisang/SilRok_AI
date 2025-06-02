from dataclasses import dataclass, field
from typing import Union

from .flag import *


@dataclass(slots=True)
class LLMInput:
    group_id: str
    conversation: str = field(default="")
    mode: str = field(default=REQUEST)
    agenda: Union[list[str], None] = field(default=None)
    num_people: Union[int, None] = field(default=None)
    meeting_topic: Union[str, None] = field(default=None)

    DONE = DONE
    REQUEST = REQUEST
    UPDATE = UPDATE

    # Override
    def __post_init__(self):
        if self.mode not in [DONE, REQUEST, UPDATE]:
            raise ValueError(
                f"Invalid mode: {self.mode}. Must be one of {DONE}, {REQUEST}, {UPDATE}."
            )
