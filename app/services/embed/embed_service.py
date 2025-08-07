import asyncio
import ray

from logging import Logger
from typing import Callable
from dependency_injector.resources import AsyncResource

from services.embed.embed import Embed
from services.embed.dto import EmbedInput, EmbedOutput


class EmbedService(AsyncResource):
    async def init(self, logger: Logger):
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")

        ray.init(ignore_reinit_error=True)

        self.logger = logger
        self.embed = Embed.remote()
        await self.embed.init.remote()

        self.logger.info("Embed service initialized")
        return self

    async def shutdown(self, _: "EmbedService") -> None:
        await self.embed.close.remote()
        self.logger.info("Embed service closed")

    async def request(self, X: EmbedInput) -> EmbedOutput:
        return await self.embed.request.remote(X)

    def request_with_callback(
        self,
        X: EmbedInput,
        callback: Callable[[EmbedOutput | None, Exception | None], None],
    ) -> None:
        async def _run() -> None:
            try:
                return await callback(await self.request(X), None)
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                return await callback(None, e)

        asyncio.create_task(_run())
