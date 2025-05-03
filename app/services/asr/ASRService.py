import asyncio
from RTWhisper import SentenceStreamer, TokenStreamer, Transcriber
from RTWhisper.data import Result
from ServerObject import ServerObject
from core import settings

from services.ThreadManagerService import ThreadManagerService

from .dto import ASRContext


class ASRService(ServerObject):

    @ThreadManagerService.object  # NOTE 서비스 끼리 참조하지 않으려고 하였으나, 이 부분은 성능상 이렇게 함
    @Transcriber.object
    @TokenStreamer.object
    @SentenceStreamer.object
    def __init__(
        self,
        thread_manager_service: ThreadManagerService,
        transcriber: Transcriber,
        token_streamer: TokenStreamer,
        sentence_streamer: SentenceStreamer,
        MIN_AUDIO_DURATION: int = settings.MIN_AUDIO_DURATION,
    ) -> None:
        super().__init__()

        self.thread_manager_service = thread_manager_service
        self.transcriber = transcriber
        self.token_streamer = token_streamer
        self.sentence_streamer = sentence_streamer

        self.__lock = asyncio.Lock()
        self.__MIN_AUDIO_DURATION = MIN_AUDIO_DURATION

    async def __transcribe_wrapper(self, asr_entity: ASRContext, func: callable):
        param = asr_entity.param
        if len(param.audio) < self.__MIN_AUDIO_DURATION:
            return

        async with self.__lock:
            result: Result = await self.thread_manager_service.submit_to_executor(
                func, param
            )

        param.update(result)
        asr_entity.completed = result.completed
        asr_entity.candidate = result.candidate

    async def transcribe_by_duration(self, asr_entity: ASRContext):
        return await self.__transcribe_wrapper(asr_entity, self.token_streamer.process)

    async def transcribe_by_sentence(self, asr_entity: ASRContext):
        return await self.__transcribe_wrapper(
            asr_entity, self.sentence_streamer.process
        )

    async def transcribe(self, asr_entity: ASRContext):
        return await self.__transcribe_wrapper(asr_entity, self.transcriber.process)
