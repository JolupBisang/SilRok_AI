import asyncio
from collections import defaultdict
import logging
import ray

from util import LRUDict

from .dto import LLMInput, LLMContext, LLMOutput
from .dto.flag import *


@ray.remote(num_cpus=1)
class LLM:
    def __init__(
        self,
        # 만약, Diarization 의 멀티프로세서 개수가 많아지면 문제 생길 수 있음
        MAX_STORAGE_SIZE: int,
        MAX_CACHE_SIZE: int,
    ):
        self.gemini = None
        self.logger = None

        self.__locks = None
        self.__storage = None
        self.__MAX_STORAGE_SIZE = MAX_STORAGE_SIZE
        self.__MAX_CACHE_SIZE = MAX_CACHE_SIZE

    def init(self):
        from containers import Container
        from core import logging_manager

        manager = Container.get_manager()
        manager.init_llm()

        self.gemini = manager.container.gemini()
        self.logger = logging_manager.generate("llm", logging.INFO)

        self.__locks = defaultdict(asyncio.Lock)
        self.__storage = LRUDict(self.__MAX_STORAGE_SIZE)
        self.__MAX_CACHE_SIZE = self.__MAX_CACHE_SIZE

    def __get_context(self, X: LLMInput) -> LLMContext:
        group_id = X.group_id
        if group_id not in self.__storage:
            self.__storage[group_id] = LLMContext(
                group_id=group_id, model=self.gemini.generate()
            )
        return self.__storage[group_id]

    async def request(self, X: LLMInput):
        group_id = X.group_id
        async with self.__locks[group_id]:
            context = self.__get_context(X)
            context.update(X)

            if (
                context.mode == UPDATE
                and len(context.conversation) < self.__MAX_CACHE_SIZE
            ):
                self.logger.debug(f"Updated conversation")
                return

            prompt = context.get_prompt()
            context.conversation = ""

            try:
                response = await context.model.send_message_async(prompt)
                self.logger.debug(f"Prompt: {prompt}")
                self.logger.debug(f"Response: {response.text}")

                return LLMOutput.from_context_and_response(X, response.text)
            except Exception as e:
                self.logger.error(f"LLM processing error: {e}")
                return LLMOutput(group_id=X.group_id)

    async def close(self):
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        ray.actor.exit_actor()
