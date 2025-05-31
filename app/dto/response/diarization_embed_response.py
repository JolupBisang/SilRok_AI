import base64
from pydantic import BaseModel

from dto.response.annotations import Embedding, UserId
from services.embed import EmbedOutput


class DiarizationEmbedResponse(BaseModel):
    user_id: UserId
    embedding: Embedding

    @staticmethod
    def from_embed_output(embed_output: EmbedOutput) -> "DiarizationEmbedResponse":
        embedding = base64.b64encode(embed_output.embedding).decode("utf-8")
        return DiarizationEmbedResponse(
            user_id=embed_output.user_id, embedding=embedding
        )
