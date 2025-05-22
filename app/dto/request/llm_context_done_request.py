from pydantic import BaseModel

from dto.request.annotations import GroupId


class LLMContextDoneRequest(BaseModel):
    group_id: GroupId
