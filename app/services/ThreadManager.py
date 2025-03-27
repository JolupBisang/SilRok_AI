from asyncio import Future
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Set

THREAD_MAX_WORKERS = 20

class ThreadManager:
  def __init__(self):
    self.__executor = ThreadPoolExecutor(max_workers=THREAD_MAX_WORKERS)
    self.__running_futures: Set[Future] = set()

  def submit_to_executor(self, fn, *args):
    fut = self.__executor.submit(fn, *args)
    afut = asyncio.wrap_future(fut)
    self.__running_futures.add(afut)
    afut.add_done_callback(self.__running_futures.remove)
    return afut

  async def close(self):
    if self.__running_futures:
      await asyncio.gather(*self.__running_futures, return_exceptions=True)
    self.__executor.shutdown(wait=True)