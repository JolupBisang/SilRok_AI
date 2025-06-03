from fastapi import Request
from pydantic import BaseModel

from dto.request.annotations import Counts, GroupId, RefersFile, UserId, UserIds


class DiarizationReferRequest(BaseModel):
    group_id: GroupId
    user_id: UserId
    user_ids: UserIds
    counts: Counts
    refers: RefersFile

    @classmethod
    async def as_file(
        cls,
        group_id: GroupId,
        user_id: UserId,
        user_ids: UserIds,
        counts: Counts,
        refers: RefersFile,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            user_ids=user_ids,
            counts=counts,
            refers=refers,
        )

    @classmethod
    async def as_stream(
        cls,
        group_id: GroupId,
        user_id: UserId,
        user_ids: UserIds,
        counts: Counts,
        refers: Request,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            user_ids=user_ids,
            counts=counts,
            refers=await refers.body(),
        )
