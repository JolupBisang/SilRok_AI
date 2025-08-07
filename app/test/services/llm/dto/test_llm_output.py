from __future__ import annotations
from typing import TYPE_CHECKING

import random

from dataclasses import dataclass

from services.llm.dto import LLMOutput

if TYPE_CHECKING:
    from services.llm.dto import LLMInput


@dataclass(slots=True)
class TestLLMOutput(LLMOutput):
    @staticmethod
    def create_random(X: LLMInput) -> "TestLLMOutput":
        agenda_len = len(X.agenda) if X.agenda else 0
        group_id = X.group_id
        context = f"This is a test context for group {group_id}."
        agenda = random.sample(range(agenda_len), random.randint(0, agenda_len))
        feedback = [
            {"user_id": f"user_{i}", "comment": f"This is a test comment {i}"}
            for i in random.sample(range(1, 6), random.randint(0, 3))
        ]
        return TestLLMOutput(
            group_id=group_id,
            context=context,
            agenda=agenda,
            feedback=feedback,
        )


__all__ = ["TestLLMOutput"]
