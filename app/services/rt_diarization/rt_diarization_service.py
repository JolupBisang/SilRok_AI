from typing import Union
import ray
import asyncio

from core import Settings, Singleton, logger

from .diarizing_asr import DiarizingASR
from .broker import Broker
from .merger import Merger
from .dto import DiarizingASRInput, MergerOutput, DiarizingASROutput


class RTDiarizationService(Singleton):
    def __init__(self):
        super().__init__()
        ray.init(
            ignore_reinit_error=True,
        )

        self.broker: Broker = None
        self.merger: Merger = None
        self.__diarizing_asr: list[DiarizingASR] = None
        self.__callbacks: dict[str:callable] = None
        self.__task:asyncio.Future = None
        self.__lock:asyncio.Lock = None

    def init(self, NUM_CONSUMERS: int = Settings.NUM_CONSUMERS):

        self.broker = Broker.remote()
        self.merger = Merger.remote()
        self.__diarizing_asr = [
            DiarizingASR.remote() for _ in range(NUM_CONSUMERS)
        ]

        self.__callbacks = {}
        self.__task = None
        self.__lock = asyncio.Lock()

        waiters = [
            self.broker.init.remote([idx for idx in range(NUM_CONSUMERS)]),
            self.merger.init.remote(self.broker)
        ]
        waiters += [consumer.init.remote(idx, self.broker) for idx, consumer in enumerate(self.__diarizing_asr)]

        logger.info(f"Service initialized with {NUM_CONSUMERS} consumers")

        return waiters

    def run(self):
        if self.__task is not None:
            raise RuntimeError("Service is already running")
        self.__task = asyncio.get_running_loop().create_task(self.__run())

        waiters = [self.merger.run.remote(),]
        waiters += [consumer.run.remote() for consumer in self.__diarizing_asr]
        return waiters

    async def __run(self):
        logger.info("Service started")
        try:
            while True:
                Y:Union[MergerOutput, DiarizingASROutput] = await self.broker.get_result.remote()
                if Y== "END":
                    break

                try:
                    async with self.__lock:
                        await self.__callbacks[Y.uuid](Y)
                except KeyError:
                    logger.warning(f"Callback not found for {Y.uuid}")
        except BaseException as e:
            logger.error(f"Error in service: {e}")
        logger.info("Service stopped")

    async def add_callback(self, sid:str, callback: callable):
        async with self.__lock:
            self.__callbacks[sid] = callback

    async def remove_callback(self, sid:str):
        async with self.__lock:
            del self.__callbacks[sid]

    async def request(self, X: DiarizingASRInput):
        await self.broker.register_diarizing_asr.remote(X)

    async def close(self):
        if self.__task is None:
            raise RuntimeError("Service is not running")
        for consumer in self.__diarizing_asr:
            await consumer.close.remote()
        await self.broker.send_sig_to_result_queue.remote("END")
        await self.merger.close.remote()
        await self.broker.close.remote()
        await self.__task
        self.__task = None
