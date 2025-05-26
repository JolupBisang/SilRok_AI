from fastapi import Request
from pydantic import BaseModel

from dto.request.annotations import GroupId, SCOffset, UserId, AudioFile

class DiarizationRequest(BaseModel):
    group_id: GroupId
    user_id: UserId
    sc_offset: SCOffset
    audio: bytes

    @classmethod
    async def as_file(
        cls,
        group_id: GroupId,
        user_id: UserId,
        audio: AudioFile,
        sc_offset: SCOffset = None,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            sc_offset=sc_offset,
            audio=audio,
        )

    @classmethod
    async def as_stream(
        cls,
        group_id: GroupId,
        user_id: UserId,
        audio: Request,
        sc_offset: SCOffset = None,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            sc_offset=sc_offset,
            audio=await audio.body(),
        )
