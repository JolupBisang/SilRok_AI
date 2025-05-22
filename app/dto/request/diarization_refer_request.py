from pydantic import BaseModel

from dto.request.annotations import GroupIdField, ReferField, UserIdField


class DiarizationReferRequest(BaseModel):
    group_id: GroupIdField
    user_id: UserIdField
    refer: ReferField
