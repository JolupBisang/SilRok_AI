from RTWhisper.data import Sentence
from dto.response import SentenceResponse
from services import ThreadManagerService
from services.diarization import DiarizationService
from services.diarization.dto import DiarizationContext
from services.diarization.dto import AudioRefer

from .dto import Metadata


class DiarizationSub:
    @DiarizationService.object
    @ThreadManagerService.object
    def __init__(
        self,
        diarization_service: DiarizationService,
        thread_manager_service: ThreadManagerService,
    ):
        self.diarization_service = diarization_service
        self.thread_manager_service = thread_manager_service

    def get_diarization_context(self, metadata: Metadata):
        return DiarizationContext.get_instance(
            metadata.user_id,
            AudioRefer.from_dict(metadata.refer),
        )

    async def service(
        self,
        metadata: Metadata,
        completed: list[Sentence],
        candidate: list[Sentence],
        dc: DiarizationContext,
    ):
        dc.update(metadata.audio, completed, candidate)
        await self.thread_manager_service.submit_to_executor(
            self.diarization_service.diarize, dc
        )

        if dc.completed or dc.candidate:
            sr = SentenceResponse.from_diarization_context(dc)
            if sr.completed or sr.candidate:
                return sr.model_dump()
        return None
