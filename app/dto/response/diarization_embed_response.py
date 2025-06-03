import base64
from typing import Any, Callable
from pydantic import BaseModel

from dto.response.annotations import Embedding, UserId
from services.embed import EmbedOutput


class DiarizationEmbedResponse(BaseModel):
    user_id: UserId
    embedding: Embedding

    # NOTE front 요청으로 임의 설정
    flag: str = "embedded"

    def to_byte(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump(exclude={"embedding"}))
        return len(bt).to_bytes(4, "big") + bt + self.embedding

    # NOTE Http Response를 위해 임시로 조치
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "embedding": base64.b64encode(self.embedding).decode("utf-8"),
            "flag": self.flag,
        }

    @staticmethod
    def from_embed_output(embed_output: EmbedOutput) -> "DiarizationEmbedResponse":
        return DiarizationEmbedResponse(
            user_id=embed_output.user_id, embedding=embed_output.embedding.tobytes()
        )
