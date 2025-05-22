from pydantic import BaseModel

from dto.request.annotations import GroupId


class LLMContextRequest(BaseModel):
    group_id: GroupId
