import asyncio
from logging import Logger
from typing import Callable
from dependency_injector.resources import AsyncResource
import numpy as np
import ray

from .embed import Embed
from .dto import EmbedInput, EmbedOutput


class EmbedService(AsyncResource):
    async def init(self, logger: Logger):
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")

        super().__init__()
        ray.init(ignore_reinit_error=True)

        self.logger = logger
        self.embed = Embed.remote()
        await self.embed.init.remote()

        return self

    async def shutdown(self, _: "EmbedService") -> None:
        await self.embed.close.remote()

    async def request(self, X: EmbedInput) -> np.ndarray:
        return await self.embed.request.remote(X)

    def request_with_callback(
        self, X: EmbedInput, callback: Callable[[EmbedOutput], None]
    ) -> None:
        async def _run() -> None:
            try:
                result = await self.request(X)
                if result is not None:
                    await callback(result)
            except Exception as e:
                print(f"Error in callback: {e}")

        asyncio.create_task(_run())
