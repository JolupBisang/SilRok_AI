import numpy as np

from ServerObject import ServerObject
from core import settings
from dto.request import SttByte, SttFile, SttDuration
from dto.response import SentenceResponse
from services.asr.dto import ASRContext
from services.asr import ASRService
from services.redis import RedisService

from .dto import TokenRedisContext


class ASRUC(ServerObject):

    @ASRService.object
    @RedisService.object
    def __init__(
        self,
        asr_service: ASRService,
        redis_service: RedisService,
        sample_rate: int = settings.MODEL_SAMPLE_RATE,
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
        trc = TokenRedisContext(group_id=group, user_id=user)
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

    # async def transcribe_by_duration_from_opus(
    #   self, audio:bytes, group:str, user:str, language:str
    # ):
    #   audio, _ = decompress_from_opus(audio)
    #   audio = bytes_to_np(io.BytesIO(audio), self.__SAMPLE_RATE)
    #   audio = np.mean(audio, axis=1) if audio.ndim > 1 else audio

    #   completed, candidate = await self.__transcribe_by_duration(
    #     audio, group=group, user=user, language=language
    #   )
    #   result = SentenceResponse.get_from_result(
    #     completed = completed,
    #     candidate = candidate
    #   )

    #   return result
