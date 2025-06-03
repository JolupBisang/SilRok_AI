import asyncio
import logging
from typing import Any, Union
import ray
from asyncio import Queue

from .dto import (
    DiarizingASRInput,
    MergerInput,
    MergerOutput,
)


@ray.remote(num_cpus=1)
class Broker:
    def __init__(
        self,
        MAX_QUEUE_SIZE: int,
    ):
        self.__group_to_pid = None
        self.__pid_to_group = None

        self.__queue_diarizing_asr = None
        self.__queue_merger = None

        self.__result = None

        self.logger = None

        self.__MAX_QUEUE_SIZE = MAX_QUEUE_SIZE

    def init(
        self,
        consumer_pid_list: list[int],
    ):
        from core import logging_manager, Config

        self.__group_to_pid = {}
        self.__pid_to_group = {pid: [] for pid in consumer_pid_list}

        self.__queue_diarizing_asr = {
            pid: Queue(maxsize=self.__MAX_QUEUE_SIZE) for pid in consumer_pid_list
        }
        self.__queue_merger = Queue(maxsize=self.__MAX_QUEUE_SIZE)
        self.__result = Queue(maxsize=self.__MAX_QUEUE_SIZE)

        self.logger = logging_manager.generate(
            "broker", Config.get_instance().config.server.log_level
        )

    def __get_pid_by_group_id(self, group_id: str):
        if group_id in self.__group_to_pid:
            return self.__group_to_pid[group_id]

        pid = min(
            self.__pid_to_group.keys(),
            key=lambda pid: len(self.__pid_to_group[pid]),
        )
        self.__group_to_pid[group_id] = pid
        self.__pid_to_group[pid].append(group_id)
        return pid

    async def register_diarizing_asr(self, X: DiarizingASRInput):
        await self.__queue_diarizing_asr[self.__get_pid_by_group_id(X.group_id)].put(X)

    async def register_merger(self, X: MergerInput):
        await self.__queue_merger.put(X)

    # async def complete_diarizing_asr(
    #     self, Y: DiarizingASROutput
    # ):
    #     # example
    #     self.__result_queue[self.__get_pid_by_group_id(Y.group_id)].put(Y)
    #     pass

    async def complete_merger(self, Y: MergerOutput):
        await self.__result.put(Y)

    async def get_diarizing_asr_task(self, pid: int) -> Union[DiarizingASRInput, Any]:
        return await self.__queue_diarizing_asr[pid].get()

    async def get_merger_task(self) -> Union[tuple[MergerInput], Any]:
        return await self.__queue_merger.get()

    async def send_sig_to_diarizing_asr_queue(self, pid: int, sig: Any):
        await self.__queue_diarizing_asr[pid].put(sig)

    async def send_sig_to_merger_queue(self, sig: Any):
        await self.__queue_merger.put(sig)

    # def full(self, Y: DiarizingASRInput):
    #     pid = self.__get_pid_by_group_id(Y.group_id)
    #     return self.__queue_diarizing_asr[pid].full() or self.__result.full()

    async def close(self):
        await asyncio.gather(*asyncio.all_tasks())
        ray.actor.exit_actor()

    async def get_result(self):
        return await self.__result.get()

    async def send_sig_to_result_queue(self, sig: Any):
        await self.__result.put(sig)
