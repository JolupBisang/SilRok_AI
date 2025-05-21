import asyncio
import numpy as np

from RTWhisper.data import Sentence
from core import Singleton
from models import Pyannote

from .dto import Context, Speak

MIN_DURATION = 8000


class Service(Singleton):

    @Pyannote.object
    def __init__(
        self,
        pyannote: Pyannote,
    ):
        super().__init__()
        self.pyannote = pyannote

    async def get_embedding(self, audio: np.ndarray):
        return await self.pyannote.get_embeddings(audio)

    # FIXME 일단 이렇게 했는데, 별로다
    def __adjust_ts(self, start: int, end: int, offset: int, max_: int):
        start = max(0, start - offset)
        end = end - offset

        duration = end - start
        if duration < MIN_DURATION:
            end = min(max_, end + MIN_DURATION - duration)
            duration = end - start
            if duration < MIN_DURATION:
                end = max(0, start - MIN_DURATION + duration)
                duration = end - start
                if duration < MIN_DURATION:
                    return -1, -1
        return start, end

    async def diarize(self, dc: Context):

        if not dc.completed and not dc.candidate:
            return

        clustering = dc.clustering
        audio = dc.audio
        offset = dc.offset
        user_id = dc.user_id

        # FIXME 이것도 별로다
        async def __filter(ary: list[Sentence], func: callable):
            last_end_time = offset
            result = []
            for sentence in ary:
                start, end = self.__adjust_ts(
                    sentence.tokens[0].start,
                    sentence.tokens[-1].end,
                    offset,
                    len(audio),
                )
                last_end_time = sentence.tokens[-1].end
                if start == -1 or end == -1:
                    continue
                predict_id, similarity = func(
                    await self.get_embedding(audio[start:end])
                )
                result.append(
                    Speak(
                        similarity=float(similarity),
                        user_id=predict_id,
                        audio_id=user_id,
                        sentence=sentence,
                    )
                )
            return result, last_end_time

        completed, last_end_time = await __filter(dc.completed, clustering.add)

        candidate, _ = await __filter(dc.candidate, clustering.get_closest)

        dc.audio = audio[last_end_time - offset :]
        dc.offset = last_end_time
        dc.completed = completed
        dc.candidate = candidate
