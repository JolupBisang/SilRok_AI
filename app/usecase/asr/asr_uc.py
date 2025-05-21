import numpy as np

from core import Settings, Singleton
from dto.request import SttByte, SttFile, SttDuration
from dto.response import SentenceResponse
from services.asr import ASRService, ASRContext
from services.redis import RedisService

from .dto import RedisContext


class ASRUC(Singleton):

    @ASRService.object
    @RedisService.object
    def __init__(
        self,
        asr_service: ASRService,
        redis_service: RedisService,
        sample_rate: int = Settings.MODEL_SAMPLE_RATE,
    ):
        super().__init__()

        self.asr_service = asr_service
        self.redis_service = redis_service

        self.__SAMPLE_RATE = sample_rate

    async def __transcribe(
        self,
        audio: np.ndarray,
        group: str,
        user: str,
        prompt: str = None,
        language: str = None,
        func: callable = None,
    ):
        trc = RedisContext(group_id=group, user_id=user)
        await self.redis_service.load(trc)

        asr_context = trc.get_asr_context()
        asr_context.update(audio, prompt=prompt, language=language)
        await func(asr_context)
        await self.redis_service.save(trc)

        return SentenceResponse.from_asr_context(asr_context)

    async def transcribe_from_bytes(self, param: SttByte | SttFile):
        asr_context = ASRContext.get_instance(
            await param.get_audio(self.__SAMPLE_RATE), param.prompt, param.language
        )
        await self.asr_service.transcribe(asr_context)
        return SentenceResponse.from_asr_context(asr_context)

    async def transcribe_by_duration_from_bytes(self, param: SttDuration):
        return await self.__transcribe(
            await param.get_audio(self.__SAMPLE_RATE),
            param.group,
            param.user,
            language=param.language,
            func=self.asr_service.transcribe_by_duration,
        )
