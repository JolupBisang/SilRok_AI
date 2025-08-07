from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio

from typing import Callable
from dependency_injector.resources import AsyncResource

from test.services.llm.dto.test_llm_output import TestLLMOutput

if TYPE_CHECKING:
    from services.llm.dto import LLMInput, LLMOutput


class TestLLMService(AsyncResource):
    # override
    async def init(self):
        return self

    # override
    async def shutdown(self, _: "TestLLMService") -> None:
        return None

    def request_with_callback(
        self,
        X: LLMInput,
        callback: Callable[[LLMOutput | None, Exception | None], None],
    ) -> None:
        async def _run() -> None:
            try:
                await callback(await self.request(X), None)
            except Exception as e:
                await callback(None, e)

        asyncio.create_task(_run())

    async def request(self, X: LLMInput) -> LLMOutput | None:
        return TestLLMOutput.create_random(X)
