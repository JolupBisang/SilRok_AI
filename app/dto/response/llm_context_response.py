from typing import Any, Callable
from pydantic import BaseModel

from dto.response.annotations import Context, GroupId
from services.llm import LLMOutput


class LLMContextResponse(BaseModel):
    group_id: GroupId
    context: Context

    # NOTE front 요청으로 임의 설정
    flag:str = "context"
    is_recap:bool = False

    def to_byte(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump())
        return len(bt).to_bytes(4, "big") + bt

    @staticmethod
    def from_llm_output(Y: LLMOutput):
        return LLMContextResponse(
            group_id=Y.group_id,
            context=Y.context,
        )
