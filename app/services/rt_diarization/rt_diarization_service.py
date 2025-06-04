from logging import Logger
from typing import Any, Callable
import ray
import asyncio
from dependency_injector.resources import AsyncResource

from .diarizing_asr import DiarizingASR
from .broker import Broker
from .merger import Merger
from .dto import DiarizingASRInput, MergerOutput, DiarizingASROutput, RTDiarizationError


class RTDiarizationService(AsyncResource):
    # override
    async def init(
        self,
        logger: Logger,
        NUM_CONSUMERS: int,
        MAX_QUEUE_SIZE: int,
        MAX_STORAGE_SIZE: int,
        MIN_AUDIO_DURATION: int,
        SAMPLE_RATE: int,
    ):
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")
        if not isinstance(NUM_CONSUMERS, int) or NUM_CONSUMERS <= 1:
            raise ValueError("NUM_CONSUMERS must be a positive integer greater than 1")
        if not isinstance(MAX_QUEUE_SIZE, int) or MAX_QUEUE_SIZE <= 1:
            raise ValueError("MAX_QUEUE_SIZE must be a positive integer greater than 1")
        if not isinstance(MAX_STORAGE_SIZE, int) or MAX_STORAGE_SIZE <= 1:
            raise ValueError(
                "MAX_STORAGE_SIZE must be a positive integer greater than 1"
            )
        if not isinstance(MIN_AUDIO_DURATION, int) or MIN_AUDIO_DURATION < 8000:
            raise ValueError(
                "MIN_AUDIO_DURATION must be a positive integer greater than or equal to 8000"
            )
        if not isinstance(SAMPLE_RATE, int) or SAMPLE_RATE < 8000:
            raise ValueError(
                "SAMPLE_RATE must be a positive integer greater than or equal to 8000"
            )

        super().__init__()
        ray.init(
            ignore_reinit_error=True,
        )

        self.logger: Logger = logger
        self.broker: Broker = Broker.remote(MAX_QUEUE_SIZE)
        self.merger: Merger = Merger.remote(MAX_STORAGE_SIZE)
        self.__diarizing_asr: list[DiarizingASR] = [
            DiarizingASR.remote(MAX_STORAGE_SIZE, MIN_AUDIO_DURATION, SAMPLE_RATE)
            for _ in range(NUM_CONSUMERS)
        ]
        self.__callbacks: dict[str:callable] = {}
        self.__task: asyncio.Future = None
        self.__lock = asyncio.Lock()

        pid = [idx for idx in range(NUM_CONSUMERS)]
        await asyncio.gather(
            *[
                self.broker.init.remote(pid),
                self.merger.init.remote(self.broker),
                *[
                    consumer.init.remote(p, self.broker)
                    for p, consumer in zip(pid, self.__diarizing_asr)
                ],
            ]
        )
        self.logger.info(f"Service initialized with {NUM_CONSUMERS} consumers")

        await self.run()

        return self

    async def shutdown(self, _: "RTDiarizationService"):
        if self.__task is None:
            raise RuntimeError("Service is not running")
        for consumer in self.__diarizing_asr:
            await consumer.close.remote()
        await self.broker.send_sig_to_result_queue.remote("END")
        await self.__task
        await self.merger.close.remote()
        await self.broker.close.remote()
        self.__task = None
        self.logger.info("Service shutdown complete")

    async def run(self):
        if self.__task is not None:
            raise RuntimeError("Service is already running")
        self.__task = asyncio.get_running_loop().create_task(self.__run())

        waiters = [
            self.merger.run.remote(),
        ]
        waiters += [consumer.run.remote() for consumer in self.__diarizing_asr]
        await asyncio.gather(*waiters)

    async def __run(self):
        self.logger.info("Service started")
        try:
            while True:
                Y: MergerOutput | DiarizingASROutput | RTDiarizationError | Any = (
                    await self.broker.get_result.remote()
                )
                if Y == "END":
                    break

                if isinstance(Y, RTDiarizationError):
                    async with self.__lock:
                        await self.__callbacks[Y.uuid](None, Y.error)
                elif isinstance(Y, MergerOutput) or isinstance(Y, DiarizingASROutput):
                    async with self.__lock:
                        await self.__callbacks[Y.uuid](Y, None)
                else:
                    self.logger.warning(f"Unknown type received: {type(Y)} and {Y}")
        except BaseException as e:
            self.logger.error(f"Error in service: {e}")
        self.logger.info("Service stopped")

    async def add_callback(
        self,
        sid: str,
        callback: Callable[
            [DiarizingASROutput | MergerOutput | None], Exception | None
        ],
    ):
        async with self.__lock:
            self.__callbacks[sid] = callback

    async def remove_callback(self, sid: str):
        async with self.__lock:
            del self.__callbacks[sid]

    async def request(self, X: DiarizingASRInput):
        await self.broker.register_diarizing_asr.remote(X)
