from logging import Logger
from typing import Callable
import ray
import asyncio
from dependency_injector.resources import AsyncResource

from .llm import LLM
from .dto import LLMInput, LLMOutput


class LLMService(AsyncResource):
    # override
    async def init(
        self,
        logger: Logger,
        MAX_STORAGE_SIZE: int,
        MAX_CACHE_SIZE: int,
    ):
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")
        if not isinstance(MAX_STORAGE_SIZE, int) or MAX_STORAGE_SIZE <= 0:
            raise ValueError("MAX_STORAGE_SIZE must be a positive integer")
        if not isinstance(MAX_CACHE_SIZE, int) or MAX_CACHE_SIZE <= 0:
            raise ValueError("MAX_CACHE_SIZE must be a positive integer")

        super().__init__()
        ray.init(ignore_reinit_error=True)

        self.logger = logger
        self.llm: LLM = LLM.remote(MAX_STORAGE_SIZE, MAX_CACHE_SIZE)
        await self.llm.init.remote()

        self.logger.info("LLM service initialized")
        return self

    # override
    async def shutdown(self, _: "LLMService") -> None:
        await self.llm.close.remote()
        self.logger.info("LLM service closed")

    def request_with_callback(
        self,
        X: LLMInput,
        callback: Callable[[LLMOutput | None, Exception | None], None],
    ) -> None:
        async def _run() -> None:
            try:
                return await callback(await self.request(X), None)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")
                return await callback(None, e)

        asyncio.create_task(_run())

    async def request(self, X: LLMInput) -> LLMOutput | None:
        return await self.llm.request.remote(X)
