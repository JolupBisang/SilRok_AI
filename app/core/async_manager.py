from asyncio import Future
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Set

from core import Singleton
from core import Settings


class AsyncManager(Singleton):
    def __init__(self, max_workers: int = Settings.THREAD_MAX_WORKERS):
        super().__init__()
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)
        self.__running_futures: Set[Future] = set()

    def submit_to_executor(self, fn: Callable, *args, **kargs) -> asyncio.Future:
        fut = self.__executor.submit(fn, *args, **kargs)
        afut = asyncio.wrap_future(fut)
        self.__running_futures.add(afut)
        afut.add_done_callback(self.__running_futures.remove)
        return afut

    async def close(self) -> None:
        if self.__running_futures:
            await asyncio.gather(*self.__running_futures, return_exceptions=True)
        self.__executor.shutdown(wait=True)
