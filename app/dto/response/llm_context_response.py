from pydantic import BaseModel

from dto.response.annotations import Context, GroupId
from services.llm import LLMOutput


class LLMContextResponse(BaseModel):
    group_id: GroupId
    context: Context

    @staticmethod
    def from_llm_output(Y: LLMOutput):
        return LLMContextResponse(
            group_id=Y.group_id,
            context=Y.context,
        )
