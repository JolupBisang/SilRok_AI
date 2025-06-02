from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class EmbedOutput:
    user_id: str
    embedding: np.ndarray

    # NOTE 위치가 좀 애매하긴 함
    def model_dump(self) -> dict:
        return {"user_id": self.user_id}
