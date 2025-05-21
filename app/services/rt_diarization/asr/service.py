from RTWhisper import SentenceStreamer, TokenStreamer, Transcriber
from RTWhisper.data import Result
from core import Settings, Singleton

from .dto import Context


class Service(Singleton):

    @Transcriber.object
    @TokenStreamer.object
    @SentenceStreamer.object
    def __init__(
        self,
        transcriber: Transcriber,
        token_streamer: TokenStreamer,
        sentence_streamer: SentenceStreamer,
        MIN_AUDIO_DURATION: int = Settings.MIN_AUDIO_DURATION,
    ) -> None:
        super().__init__()

        self.transcriber = transcriber
        self.token_streamer = token_streamer
        self.sentence_streamer = sentence_streamer

        self.__MIN_AUDIO_DURATION = MIN_AUDIO_DURATION

    def __transcribe_wrapper(self, asr_entity: Context, func: callable):
        param = asr_entity.param
        if len(param.audio) < self.__MIN_AUDIO_DURATION:
            return

        result: Result = func(param)

        param.update(result)
        asr_entity.completed = result.completed
        asr_entity.candidate = result.candidate

    def transcribe_by_duration(self, asr_entity: Context):
        return self.__transcribe_wrapper(asr_entity, self.token_streamer.process)

    def transcribe_by_sentence(self, asr_entity: Context):
        return self.__transcribe_wrapper(asr_entity, self.sentence_streamer.process)

    def transcribe(self, asr_entity: Context):
        return self.__transcribe_wrapper(asr_entity, self.transcriber.process)
