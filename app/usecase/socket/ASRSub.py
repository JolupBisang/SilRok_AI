from dto.response import SentenceResponse
from services.asr import ASRService
from services.asr.dto import ASRContext

from .dto import Metadata


class ASRSub:
    @ASRService.object
    def __init__(
        self,
        asr_service: ASRService,
    ):
        self.asr_service = asr_service

    async def service(self, metadata: Metadata, ac: ASRContext):
        ac.update(metadata.audio)
        await self.asr_service.transcribe_by_duration(ac)

        if ac.completed or ac.candidate:
            return SentenceResponse.from_asr_context(ac).model_dump()
        return None
