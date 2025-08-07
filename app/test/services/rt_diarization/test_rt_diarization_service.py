from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio

from typing import Callable, Any
from dependency_injector.resources import AsyncResource

from test.services.rt_diarization.dto import TestDiarizingASROutput

from services.rt_diarization.dto import (
    DiarizingASRInput,
    DiarizingASROutput,
    MergerOutput,
    RTDiarizationError,
)

if TYPE_CHECKING:
    pass


class TestRTDiarizationService(AsyncResource):
    # override
    async def init(self):
        self.__callbacks: dict[
            str : Callable[[DiarizingASROutput | MergerOutput | None], Exception | None]
        ] = {}
        self.__queue: asyncio.Queue = asyncio.Queue()
        self.__task: asyncio.Future = None
        self.__lock = asyncio.Lock()

        await self.run()
        return self

    async def shutdown(self, _: "TestRTDiarizationService") -> None:
        self.__queue.put_nowait("END")
        if self.__task is None:
            raise RuntimeError("Service is not running")
        await self.__task
        self.__task = None

    async def run(self):
        if self.__task is not None:
            raise RuntimeError("Service is already running")
        self.__task = asyncio.get_running_loop().create_task(self.__run())

    async def __run(self):
        while True:
            Y: MergerOutput | DiarizingASROutput | RTDiarizationError | Any = (
                await self.__queue.get()
            )
            if Y == "END":
                break

            try:
                if isinstance(Y, RTDiarizationError):
                    async with self.__lock:
                        await self.__callbacks[Y.uuid](None, Y.error)
                elif isinstance(Y, MergerOutput) or isinstance(Y, DiarizingASROutput):
                    async with self.__lock:
                        await self.__callbacks[Y.uuid](Y, None)
            except Exception as e:
                print(e)

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
        async with self.__lock:
            await self.__queue.put(TestDiarizingASROutput.create_random(X))


__all__ = ["RTDiarizationService"]
