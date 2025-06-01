from pydantic import BaseModel

from dto.response.annotations import Context, GroupId
from services.llm import LLMOutput


class LLMContextResponse(BaseModel):
    group_id: GroupId
    context: Context

    # NOTE front 요청으로 임의 설정
    flag:str = "context"
    is_recap:bool = False

    @staticmethod
    def from_llm_output(Y: LLMOutput):
        return LLMContextResponse(
            group_id=Y.group_id,
            context=Y.context,
        )
