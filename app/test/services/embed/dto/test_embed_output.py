from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

from dataclasses import dataclass

from services.embed.dto.embed_output import EmbedOutput

if TYPE_CHECKING:
    from services.embed.dto.embed_input import EmbedInput


@dataclass(slots=True)
class TestEmbedOutput(EmbedOutput):
    @staticmethod
    def create_random(X: EmbedInput) -> "TestEmbedOutput":
        return TestEmbedOutput(
            user_id=X.user_id, embedding=np.random.rand(512).astype(np.float32)
        )


__all__ = ["TestEmbedOutput"]
