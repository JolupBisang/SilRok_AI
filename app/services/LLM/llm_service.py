import ray
import asyncio

from core import Singleton, logger

from .llm import LLM
from .dto import LLMInput, LLMOutput


class LLMService(Singleton):
    def __init__(
        self,
    ):
        super().__init__()
        ray.init(
            ignore_reinit_error=True,
        )

        self.llm: LLM = None
        self.__callbacks: dict[str:callable] = None
        self.__task: asyncio.Future = None
        self.__lock: asyncio.Lock = None

    def init(self):
        self.llm = LLM.remote()
        waiters = [self.llm.init.remote()]

        self.__callbacks = {}
        self.__task = None
        self.__lock = asyncio.Lock()

        logger.info("Service initialized")

        return waiters

    def run(self):
        if self.__task is not None:
            raise RuntimeError("Service is already running")
        self.__task = asyncio.get_running_loop().create_task(self.__run())
        return [self.llm.run.remote()]

    async def __run(self):
        logger.info("Service started")
        try:
            while True:
                Y: LLMOutput = await self.llm.get_result.remote()
                if Y == "END":
                    break
                try:
                    async with self.__lock:
                        await self.__callbacks[Y.uuid](Y)
                except Exception as e:
                    logger.error(f"Callback not found for {e}")
        except BaseException as e:
            logger.error(f"Error in service: {e}")
        logger.info("Service stopped")

    async def add_callback(self, sid:str, callback: callable):
        async with self.__lock:
            self.__callbacks[sid] = callback

    async def remove_callback(self, sid: str):
        async with self.__lock:
            del self.__callbacks[sid]

    async def request(self, X: LLMInput):
        await self.llm.register.remote(X)

    async def close(self):
        if self.__task is not None:
            await self.llm.send_sig_to_result_queue.remote("END")
            await self.llm.close.remote()
            await self.__task
            self.__task = None
