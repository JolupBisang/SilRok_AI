import logging
import numpy as np
import ray
import asyncio
import traceback

from RTWhisper import TokenStreamer
from RTWhisper.data import Result
from RTWhisper.data import Sentence
from util import LRUDict

from .broker import Broker
from .dto import (
    MergerInput,
    DiarizingASRContext,
    DiarizingASRInput,
    DiarizingASROutput,
    Speak,
)

MIN_DURATION = 8000


@ray.remote(num_cpus=1, num_gpus=0.23, memory=5 * 1024**3)
class DiarizingASR:
    def __init__(
        self,
        MAX_STORAGE_SIZE: int,
        MIN_AUDIO_DURATION: int,
        SAMPLE_RATE: int,
    ):
        self.__PID = None
        self.broker = None
        self.asr = None
        self.pyannote = None
        self.logger = None
        self.__task = None
        self.__storage = None
        self.__lock = None

        self.__MAX_STORAGE_SIZE = MAX_STORAGE_SIZE
        self.__MIN_AUDIO_DURATION = MIN_AUDIO_DURATION
        self.__SAMPLE_RATE = SAMPLE_RATE

    def init(
        self,
        pid: int,
        broker: Broker,
    ):
        from containers import Container
        from core import logging_manager

        manager = Container.get_manager()
        manager.init_diarization()

        self.__PID = pid
        self.broker = broker
        self.asr = TokenStreamer.get_instance()
        self.pyannote = manager.container.pyannote()
        self.logger = logging_manager.generate("diarizing_asr", logging.INFO)
        self.__task = None
        self.__storage = LRUDict(self.__MAX_STORAGE_SIZE)
        self.__lock = LRUDict(self.__MAX_STORAGE_SIZE)

        self.logger.info("Diarizing ASR initialized")

    def __get_lock(self, X: DiarizingASRInput):
        key = (X.group_id, X.user_id)
        if key not in self.__lock:
            self.__lock[key] = asyncio.Lock()
        return self.__lock[key]

    def run(self):
        if self.__task is not None:
            raise RuntimeError("Consumer is already running")
        loop = asyncio.get_running_loop()
        # NOTE 2개가 적당하고, 동적 조절 필요 없다고 생각해서 하드코딩 함
        # TODO 이렇게  하긴 했는데,, 생각해보니 추론 자체가 코루틴이 아님, 일단 두고 추후 수정할 것
        # TODO CUDA 자체는 커널 호출 자체가 질렬로 동작함. 따라서, RTWhisper 내부에서 CPU 바운드와 GPU 바운드를 분리 하고, GPU 바운드 작업을 다른 RAY actor로 분리하는게 맞음
        self.__task = [loop.create_task(self.__run()), loop.create_task(self.__run())]

    # TODO 에초에, ray에서 큐잉을 해줌. 즉 내부에서 따로 만든 이러한 큐잉 로직은 필요가 없음. 제거하고, remote 함수 호출식으로 변경할 것
    async def __run(self):
        self.logger.info("Diarizing ASR consumer started")
        try:
            while True:
                X: DiarizingASRInput = await self.broker.get_diarizing_asr_task.remote(
                    self.__PID
                )
                if X == "END":
                    break
                self.logger.debug(f"Diarizing ASR X received")

                async with self.__get_lock(X):
                    context = self.__get_context(X)
                    context.update(X)
                    merger_X, Y = await self.__service(context)

                # 임의 로직
                merger_X.must_return = X.must_return
                if merger_X.must_return or merger_X.completed or merger_X.candidate:
                    self.broker.register_merger.remote(merger_X)

                self.logger.debug(f"Diarizing ASR processed")
        except BaseException as e:
            self.logger.error(f"Diarizing ASR consumer error: {e}")
        self.logger.info("Diarizing ASR consumer stopped")

    async def close(self):
        if self.__task is not None:
            self.broker.send_sig_to_diarizing_asr_queue.remote(self.__PID, "END")
            self.broker.send_sig_to_diarizing_asr_queue.remote(self.__PID, "END")
            await asyncio.gather(*self.__task)
            self.__task = None
            ray.actor.exit_actor()

    def __get_context(self, X: DiarizingASRInput) -> DiarizingASRContext:
        group_id = X.group_id
        user_id = X.user_id
        if group_id not in self.__storage:
            self.__storage[group_id] = {}
        if user_id not in self.__storage[group_id]:
            self.__storage[group_id][user_id] = (
                DiarizingASRContext.from_diarizing_asr_input(X)
            )

        return self.__storage[group_id][user_id]

    async def __service(self, context: DiarizingASRContext):
        try:
            # self.logger.info("ASR start")
            self.__asr(context)
            # self.logger.info("ASR done")
            # FIXME 여기서 refer가 없다면, 오류걸림.
            await self.__diarize(context)
            # self.logger.info("Diarization done")
        except Exception as e:
            self.logger.error(f"Diarizing ASR service error: {e}")
            self.logger.error(traceback.format_exc())
            raise e

        merger_X = MergerInput.from_diarizing_asr_context(context)
        Y = DiarizingASROutput.from_diarizing_asr_context(context)

        return merger_X, Y

    def __asr(self, context: DiarizingASRContext):
        param = context.param
        if len(param.audio) < self.__MIN_AUDIO_DURATION:
            return

        result: Result = self.asr.process(param)

        param.update(result)
        context.asr_completed = result.completed
        context.asr_candidate = result.candidate

    async def __diarize(self, context: DiarizingASRContext):
        if not context.asr_completed and not context.asr_candidate:
            return

        clustering = context.clustering
        audio = context.audio
        offset = context.offset
        user_id = context.user_id

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
                    await self.__get_embedding(audio[start:end])
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

        completed, last_end_time = await __filter(context.asr_completed, clustering.add)

        candidate, _ = await __filter(context.asr_candidate, clustering.get_closest)

        context.audio = audio[last_end_time - offset :]
        context.offset = last_end_time
        context.diarization_completed = completed
        context.diarization_candidate = candidate

    async def __get_embedding(self, audio: np.ndarray):
        return await self.pyannote.get_embeddings(audio, self.__SAMPLE_RATE)

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
