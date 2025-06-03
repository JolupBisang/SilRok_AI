import asyncio
import logging
import ray

from util import LRUDict

from .broker import Broker
from .dto import MergerContext, MergerInput, MergerOutput, Speak


@ray.remote(num_cpus=1)
class Merger:
    def __init__(
        self,
        MAX_STORAGE_SIZE: int,
    ):
        self.broker = None
        self.logger = None
        self.__task = None
        self.__storage = None

        self.__MAX_STORAGE_SIZE = MAX_STORAGE_SIZE

    def init(
        self,
        broker: Broker,
    ):
        from core import logging_manager, Config

        self.broker = broker
        self.logger = logging_manager.generate(
            "merger", Config.get_instance().config.server.log_level
        )
        self.__task = None
        self.__storage = LRUDict(self.__MAX_STORAGE_SIZE)

        self.logger.info("Merger initialized")

    def run(self):
        if self.__task is not None:
            raise RuntimeError("Merger is already running")
        self.__task = asyncio.get_running_loop().create_task(self.__run())

    def __get_context(self, X: MergerInput):
        group_id = X.group_id
        if group_id in self.__storage:
            return self.__storage[group_id]
        context = MergerContext.from_merger_input(X)
        self.__storage[group_id] = context
        return context

    async def __run(self):
        self.logger.info("Merger consumer started")
        try:
            while True:
                # TODO change this call
                X: MergerInput = await self.broker.get_merger_task.remote()
                if X == "END":
                    break
                self.logger.debug(f"Merger X received")

                context = self.__get_context(X)
                context.update(X)

                context.set_result(
                    self.__merge(context.completed),
                    self.__merge(context.candidate),
                )

                Y = MergerOutput.from_merger_context(context)
                # Must return 은 임의로 한 거임
                if X.must_return or Y.completed or Y.candidate:
                    await self.broker.complete_merger.remote(
                        MergerOutput.from_merger_context(context)
                    )

                self.logger.debug(f"Merger processed")
        except BaseException as e:
            self.logger.error(f"Merger consumer error: {e}")
        self.logger.info("Merger consumer stopped")

    # TODO  제대로된 정렬 및 선택 알고리즘 필요
    def __merge(self, speaks: list[Speak], boundary: int = 2):
        if len(speaks) == 0:
            return []

        speaks_groups = [[speaks[0]]]
        cnt_idx = 0
        for speak in speaks[1:]:
            similarities = []
            for i in range(
                max(0, cnt_idx - boundary), min(cnt_idx + boundary, len(speaks_groups))
            ):
                similarities.append((i, speaks_groups[i][-1].similar(speak)))
            max_arg = max(range(len(similarities)), key=lambda x: similarities[x][1])
            if similarities[max_arg][1] < 0.5:
                speaks_groups.append([speak])
                cnt_idx += 1
            else:
                speaks_groups[max_arg].append(speak)

        return [max(sg, key=lambda x: x.similarity) for sg in speaks_groups]

    async def close(self):
        if self.__task is not None:
            self.broker.send_sig_to_merger_queue.remote("END")
            await self.__task
            self.__task = None
            ray.actor.exit_actor()
