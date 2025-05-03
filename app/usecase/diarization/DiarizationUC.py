from ServerObject import ServerObject
from core import settings
from services.diarization import DiarizationService
from util.util import bytes_to_np


class DiarizationUC(ServerObject):

    @DiarizationService.object
    def __init__(
        self,
        diarization_service: DiarizationService,
        SAMPLE_RATE: int = settings.MODEL_SAMPLE_RATE,
    ):
        super().__init__()
        self.diarization_service = diarization_service

        self.__SAMPLE_RATE = SAMPLE_RATE

    async def get_embedding(self, data: bytes):
        audio = bytes_to_np(data, self.__SAMPLE_RATE)
        embedding = await self.diarization_service.get_embedding(audio)
        return embedding.tobytes()
