from fastapi import Request
from pydantic import BaseModel

from dto.request.annotations import GroupId, UserId, AudioFile

class DiarizationRequest(BaseModel):
    group_id: GroupId
    user_id: UserId
    audio: bytes

    @classmethod
    async def as_file(
        cls,
        group_id: GroupId,
        user_id: UserId,
        audio: AudioFile,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            audio=audio,
        )

    @classmethod
    async def as_stream(
        cls,
        group_id: GroupId,
        user_id: UserId,
        audio: Request,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            audio=await audio.body(),
        )
