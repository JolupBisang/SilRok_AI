from typing import Callable
import ray
import asyncio
from asyncio import Future

from core import Singleton, logger

from .llm import LLM
from .dto import LLMInput, LLMOutput


class LLMService(Singleton):
    def __init__(self):
        super().__init__()
        ray.init(ignore_reinit_error=True)
        self.llm: LLM | None = None

    async def init(self) -> None:
        self.llm = LLM.remote()
        await self.llm.init.remote()

    def request_with_callback(
        self, X: LLMInput, callback: Callable[[LLMOutput], None]
    ) -> None:
        async def _run() -> None:
            try:
                result = await self.request(X)
                if result is not None:
                    await callback(result)
            except Exception as e:
                logger.error(f"Error in callback: {e}")

        asyncio.create_task(_run())

    async def request(self, X: LLMInput) -> LLMOutput | None:
        return await self.llm.request.remote(X)

    async def close(self) -> None:
        await self.llm.close.remote()
