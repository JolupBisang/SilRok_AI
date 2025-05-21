import logging
import ray
import asyncio

from core import Settings
from util import LRUDict

from .asr import ASRService
from .diarization import DiarizationService
from .broker import Broker
from .dto import MergerInput, DiarizingASRContext, DiarizingASRInput, DiarizingASROutput


@ray.remote(num_cpus=1, num_gpus=1, memory=5 * 1024**3)
class DiarizingASR:
    def __init__(self):
        self.__PID = None
        self.broker = None
        self.asr_service = None
        self.diarization_service = None
        self.logger = None
        self.__task = None
        self.__storage = None

    def init(
        self,
        pid: int,
        broker: Broker,
        MAX_STORAGE_SIZE: int = Settings.MAX_STORAGE_SIZE,
    ):
        from core import logging_manager

        self.__PID = pid
        self.broker = broker
        self.asr_service = ASRService.get_instance()
        self.diarization_service = DiarizationService.get_instance()
        self.logger = logging_manager.generate("diarizing_asr", logging.INFO)
        self.__task = None
        self.__storage = LRUDict(MAX_STORAGE_SIZE)

        self.logger.info("Diarizing ASR initialized")

    def run(self):
        if self.__task is not None:
            raise RuntimeError("Consumer is already running")
        self.__task = asyncio.get_running_loop().create_task(self.__run())

    def __get_context(self, X: DiarizingASRInput):
        group_id = X.group_id
        if group_id in self.__storage:
            return self.__storage[group_id]
        context = DiarizingASRContext.from_diarizing_asr_input(X)
        self.__storage[group_id] = context
        return context

    async def __service(self, context: DiarizingASRContext):
        # self.logger.info("ASR start")
        self.asr_service.transcribe_by_duration(context.asr_context)
        # self.logger.info("ASR done")
        context.update_diarization()
        await self.diarization_service.diarize(context.diarization_context)
        # self.logger.info("Diarization done")

        merger_X = MergerInput.from_diarizing_asr_context(context)
        Y = DiarizingASROutput.from_diarizing_asr_context(context)

        return merger_X, Y

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

                context = self.__get_context(X)
                context.update(X)
                merger_X, Y = await self.__service(context)

                if merger_X.completed or merger_X.candidate:
                    self.broker.register_merger.remote(merger_X)

                self.logger.debug(f"Diarizing ASR processed")
        except BaseException as e:
            self.logger.error(f"Diarizing ASR consumer error: {e}")
        self.logger.info("Diarizing ASR consumer stopped")

    async def close(self):
        if self.__task is not None:
            self.broker.send_sig_to_diarizing_asr_queue.remote(self.__PID, "END")
            await self.__task
            self.__task = None
            ray.actor.exit_actor()
