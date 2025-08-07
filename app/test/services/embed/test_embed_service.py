from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
from typing import Callable

from dependency_injector.resources import AsyncResource
from test.services.embed.dto import TestEmbedOutput

if TYPE_CHECKING:
    from services.embed.dto.embed_input import EmbedInput
    from services.embed.dto.embed_output import EmbedOutput


class TestEmbedService(AsyncResource):
    async def init(self):
        return self

    async def shutdown(self, _: "TestEmbedService") -> None:
        return None

    async def request(self, X: EmbedInput) -> EmbedOutput:
        return TestEmbedOutput.create_random(X)

    def request_with_callback(
        self,
        X: EmbedInput,
        callback: Callable[[EmbedOutput | None, Exception | None], None],
    ) -> None:
        async def _run() -> None:
            try:
                return await callback(await self.request(X), None)
            except Exception as e:
                return await callback(None, e)

        asyncio.create_task(_run())


__all__ = ["TestEmbedService"]
