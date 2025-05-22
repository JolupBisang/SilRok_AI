from pydantic import BaseModel

from dto.response.annotations import Embedding

class DiarizationEmbedResponse(BaseModel):
    embedding:Embedding
